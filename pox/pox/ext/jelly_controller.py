import math
from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.proto.arp_responder as arp
import pickle
import random
import time
import networkx as nx
from itertools import islice
import pox.openflow.spanning_tree as st
from pox.lib.addresses import IPAddr

log = core.getLogger()


def ip_to_val(ip):
    byte_list = ip.split('.')
    val = 0
    for i in range(len(byte_list)):
        idx = len(byte_list) - i - 1 
        val |= (int(byte_list[idx]) << (i * 8))

    return val


def index(ip_val):
    return ip_val & 0xff

def level(ip_val):
    return (ip_val >> 8) & 0b11

def location(ip_val):
    return (ip_val >> 10) & 0x3fff


class TopoSwitch (object):
  def __init__ (self, connection, dpid, topo):

    self.connection = connection
    self.graph_name = 's' + str(int(dpid) - 1)
    self.TOPO = topo
    self.ip = topo['switch_to_ip'][self.graph_name]

    log.info("Switch " + self.graph_name + " set up...")
    connection.addListeners(self)


  def get_neighbor_ip_map(self):
    out = {}
    neighbors = self.TOPO['graph'][self.graph_name].keys()
    for h in self.TOPO['graph'].nodes(data='ip'):
      if h[0] in neighbors:
        out[h[0]] = h[1]

    return out


  def resend_packet (self, packet_in, out_port):
    msg = of.ofp_packet_out()
    msg.data = packet_in

    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    self.connection.send(msg)


  def _handle_PacketIn (self, event):

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    ip_val = ip_to_val(self.ip)
    lvl, idx, loc = level(ip_val), index(ip_val), location(ip_val)
    # log.info("switch num " + self.graph_name + ", ip is " + self.ip)    
    # log.info("level: %d index: %d location: %s" % (lvl, idx, bin(loc)))

    ipv4 = packet.find('ipv4')
    if ipv4 is not None:
      log.info("")
      log.info("SWITCH " + self.graph_name + ": " + str(ipv4))

      dstip = ipv4.dstip
      srcip = ipv4.srcip
      dest_location = location(ip_to_val(dstip.toStr()))
      log.info("src: %s, dest: %s, dest_location: %s" % (srcip, dstip, bin(dest_location)))

      b = int(math.ceil(math.log((self.TOPO['n_ports'] / 2), 2)))
      sw_prefix, dest_prefix = (loc >> (b * lvl)), (dest_location >> (b * lvl)) 
      log.info("switch_prefix: %s, dest_prefix: %s" % (sw_prefix, dest_prefix))

      if sw_prefix == dest_prefix: # route downwards

          if lvl == 0: # sending to a host
            hosts = self.TOPO['graph'].nodes(data='ip')
            for h in hosts:
              if h[1] == dstip:
                dsthost = h[0]

            out_port = self.TOPO['outport_mappings'][(self.graph_name, dsthost)]
            log.info("routing to host out of port %s" % (str(out_port)))
            self.resend_packet(packet_in, out_port)

          else: # find the right switch to forward to
            next_prefix = dest_location >> (b * (lvl - 1))
            next_bits = next_prefix & ((2 ** b) - 1)
            log.info("routing downwards, next bits: %s" % bin(next_bits))

            neighbor_ips = self.get_neighbor_ip_map()
            for k, v in neighbor_ips.items():
                if (location(ip_to_val(v)) >> (b * (lvl - 1))) == next_prefix:
                    out_port = self.TOPO['outport_mappings'][(self.graph_name, k)]
                    log.info("routing down to switch %s out of port %s" % (k, out_port))
                    self.resend_packet(packet_in, out_port)
                    break

      else: # route upwards
        log.info("routing upwards from level %d to level %d" % (lvl, lvl + 1))

        neighbor_ips = self.get_neighbor_ip_map()
        upper_level = []
        for k, v in neighbor_ips.items():
            log.info("ip: %s level: %d" % (k, level(ip_to_val(v))))
            if level(ip_to_val(v)) == lvl + 1:
                upper_level.append(k)

        random_switch = random.choice(upper_level)
        out_port = self.TOPO['outport_mappings'][(self.graph_name, random_switch)]
        log.info("routing up to switch %s out of port %s" % (random_switch, out_port))
        self.resend_packet(packet_in, out_port)

    '''          
      hosts = self.TOPO['graph'].nodes(data='ip')
      for host in hosts:
        if host[1] == srcip:
          srchost = host[0]
        if host[1] == dstip:
          dsthost = host[0]
      log.info("src host: " + str(srchost) + ", dsthost: " + str(dsthost))
    
      packet_paths = self._get_paths(srchost, dsthost)
      path = packet_paths[packet_id % len(packet_paths)]
      next_host_index = path.index(self.graph_name) + 1

      outport = self.TOPO['outport_mappings'][(self.graph_name, path[next_host_index])]
      log.info("Sending packet " + str(packet_id) + " from " + self.graph_name + " to " + str(path[next_host_index]) + " on port " + str(outport))
      self.resend_packet(packet_in, outport)
    '''

    '''
    tcpp = packet.find('tcp')
    if tcpp is not None:
      log.info(tcpp)

      msg = of.ofp_flow_mod()
      msg.priority = 42
      msg.match.dl_type = 0x800
      msg.match.nw_proto = 6
      msg.match.tp_src = tcpp.srcport #get src port
      ipv4 = packet.find('ipv4')
      if ipv4 is not None: #should not be none, cuz if its TCP, it has to be IP as well
        srcip = ipv4.srcip
        dstip = ipv4.dstip
        msg.match.nw_src = IPAddr(ipv4.srcip)
        msg.match.nw_dst = IPAddr(ipv4.dstip)
        hosts = self.TOPO['graph'].nodes(data='ip')
        for host in hosts:
          if host[1] == srcip:
            srchost = host[0]
          if host[1] == dstip:
            dsthost = host[0]
        outport = self.act_like_switch(packet, packet_in, event, srchost, dsthost, tcpp.srcport)
        msg.actions.append(of.ofp_action_output(port = outport))
        self.connection.send(msg)
    '''


def launch (p):
    
  topo = pickle.load(open(p))

  def start_switch (event):
    log.info("Controlling %s" % (event.connection,))
    log.info("DPID is "  + str(event.dpid))
    TopoSwitch(event.connection, event.dpid, topo)

  core.openflow.addListenerByName("ConnectionUp", start_switch)
