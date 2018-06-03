import copy
import math
from pox.core import core
from pox.lib.recoco import Timer
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

class SwitchList (object):
  def __init__(self):
    self.switches = []

  def add(self, o):
    self.switches.append(o)

  def get_list(self):
    return self.switches

  def get_elem(self, i):
    return self.switches[i]


def handle_StartPushback(switch, pb_id, from_switch, failed_prefix, failed_level, stack):
    log.debug("SWITCH %s HANDLING PB MESSAGE WITH ID %d" % (switch.graph_name, pb_id))
    if pb_id in switch.seen_pbs:
        log.debug("    already seen pb_id")
        return # stop cycles
    else:
        switch.seen_pbs.append(pb_id)

    ip_val = ip_to_val(switch.ip)
    lvl, idx, loc = level(ip_val), index(ip_val), location(ip_val)

    forwarded = False
    if lvl >= failed_level: # if below level, we can just reroute
        b = int(math.ceil(math.log((switch.TOPO['n_ports'] / 2), 2)))
        curr_prefix, fail_prefix = (loc >> (b * lvl)), (failed_prefix >> (b * lvl))

        if curr_prefix == fail_prefix: # failure below, send pushback to all neighbors
            valid_neighbors = [k for k,_ in switch.get_neighbor_ip_map().items() if k not in switch.dead_switches and k != from_switch]
        else: # failure in other subtree, only push down if necessary (not up)
            valid_neighbors = [k for k,_ in switch.get_lower_neighbors() if k not in switch.dead_switches and k != from_switch]

        # same stack prefix as failure -- push notification to all other non-failed neighors and repeat
        # assumes L=2 (sorry :( 0% generalization here)
        if lvl == 2 or (curr_prefix % 2 == 0 and stack == 'A') or (curr_prefix % 2 == 1 and stack == 'B'): 
            new_from_switch = switch.graph_name

            for s in core.list.get_list():
                if s.graph_name in valid_neighbors:
                    log.debug("    sending pushback message from switch %s to switch %s" % (switch.graph_name, s.graph_name))
                    forwarded = True
                    handle_StartPushback(s, pb_id, new_from_switch, failed_prefix, failed_level, stack)

    # else do nothing because the message is installed in pb_messages and will be used to reroute
    if not forwarded:
        log.debug("Installing state on switch %s" % (switch.graph_name,))
        switch.pb_messages[failed_prefix] = {
            'from_switch': from_switch,
            'failed_prefix': failed_prefix,
            'failed_level': failed_level,
            'stack': stack,
        }


class TopoSwitch (object):
  def __init__ (self, connection, dpid, topo):

    self.connection = connection
    self.graph_name = 's' + str(int(dpid) - 1)
    self.TOPO = topo
    self.ip = topo['switch_to_ip'][self.graph_name]
    self.dead_switches = []
    self.pre_dead_switches = []

    self.pb_messages = {}
    self.seen_pbs = []
    self.packets_sent = 0

    log.info("Switch " + self.graph_name + " set up...")
    connection.addListeners(self)

    # Timer(0.000200, self.stats_cb, recurring=True)


  '''
  def stats_cb(self):
    if self.packets_sent != 0:
        # log.info("[STATS] packets sent since last time: " + str(self.packets_sent))
        ABCDE += self.packets_sent
        self.packets_sent = 0
  '''


  def get_neighbor_ip_map(self):
    out = {}
    neighbors = self.TOPO['graph'][self.graph_name].keys()
    for h in self.TOPO['graph'].nodes(data='ip'):
      if h[0] in neighbors:
        out[h[0]] = h[1]

    return out


  def get_upper_neighbors(self):
    ip_val = ip_to_val(self.ip)
    lvl, idx, loc = level(ip_val), index(ip_val), location(ip_val)

    neighbor_ips = self.get_neighbor_ip_map()
    upper_level = [(k,v) for k,v in neighbor_ips.items() if level(ip_to_val(v)) == lvl + 1]

    return upper_level

  def get_lower_neighbors(self):
    ip_val = ip_to_val(self.ip)
    lvl, idx, loc = level(ip_val), index(ip_val), location(ip_val)

    neighbor_ips = self.get_neighbor_ip_map()
    lower_level = [(k,v) for k,v in neighbor_ips.items() if level(ip_to_val(v)) == lvl - 1]
    
    return lower_level 


  def resend_packet (self, packet_in, out_port):
    msg = of.ofp_packet_out()
    msg.data = packet_in

    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    self.packets_sent += 1
    self.connection.send(msg)

  
  def _handle_ConnectionDown (self, event):
    log.info("Killing switch %s" % (event.connection,))

    pb_id = random.randint(1, 1000000000)
    switches = core.list.get_list()
    log.info("AXXX")
    for s in switches:
      s.pre_update_down_switches(event.dpid)
      '''
      core.callDelayed(0.101, s.update_down_switches, event.dpid, pb_id)
      '''
      # s.update_down_switches(event.dpid, pb_id)


  def pre_update_down_switches(self, dpid):
    dead_switch_name = 's' + str(int(dpid) - 1)
    self.pre_dead_switches.append(dead_switch_name)


  def update_down_switches(self, dpid, pb_id):
    log.info("telling switch " + self.graph_name + " that switch with dpid " + str(dpid) + " is down")
    dead_switch_name = 's' + str(int(dpid) - 1)
    self.dead_switches.append(dead_switch_name)
    self.pre_dead_switches.remove(dead_switch_name)
    # log.info("these are the dead switches now " + str(self.dead_switches))
    log.info("BXXX")

    ip_val = ip_to_val(self.ip)
    lvl, idx, loc = level(ip_val), index(ip_val), location(ip_val)

    failed_val = ip_to_val(self.TOPO['switch_to_ip'][dead_switch_name])
    failed_lvl, failed_idx, failed_loc = level(failed_val), index(failed_val), location(failed_val)

    b = int(math.ceil(math.log((self.TOPO['n_ports'] / 2), 2)))
    failed_prefix = (failed_loc >> (b * failed_lvl))

    if failed_lvl != 2: # specify subtree type
      if failed_prefix % 2 == 0: # A subtree 
        stack = "A" 
      else: # B subtree
        stack = "B"
    else:
        stack = ""

    for k, _ in self.get_lower_neighbors():
      if k == dead_switch_name:
        core.callDelayed(0.025, handle_StartPushback, self, pb_id, dead_switch_name, failed_prefix, failed_lvl, stack)
    
    
  def _handle_PacketIn (self, event):

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return
    # log.info("Incoming packet at switch " + self.graph_name + " at port " + str(event.port))
    packet_in = event.ofp # The actual ofp_packet_in message.

    ip_val = ip_to_val(self.ip)
    lvl, idx, loc = level(ip_val), index(ip_val), location(ip_val)
    # log.info("switch num " + self.graph_name + ", ip is " + self.ip)    
    # log.info("level: %d index: %d location: %s" % (lvl, idx, bin(loc)))

    ipv4 = packet.find('ipv4')
    if ipv4 is not None:
      log.info("SWITCH " + self.graph_name + ": " + str(ipv4))

      dstip = ipv4.dstip
      srcip = ipv4.srcip
      dest_location = location(ip_to_val(dstip.toStr()))
      log.info("src: %s, dest: %s, dest_location: %s" % (srcip, dstip, bin(dest_location)))

      b = int(math.ceil(math.log((self.TOPO['n_ports'] / 2), 2)))
      sw_prefix, dest_prefix = (loc >> (b * lvl)), (dest_location >> (b * lvl)) 
      # log.info("switch_prefix: %s, dest_prefix: %s" % (sw_prefix, dest_prefix))

      if sw_prefix == dest_prefix or lvl == 2: # route downwards

          if lvl == 0: # sending to a host
            hosts = self.TOPO['graph'].nodes(data='ip')
            for h in hosts:
              if h[1] == dstip:
                dsthost = h[0]

            out_port = self.TOPO['outport_mappings'][(self.graph_name, dsthost)]
            log.info("routing to host %s out of port %s" % (str(dsthost), str(out_port)))
            self.resend_packet(packet_in, out_port)

          else: # find the right switch to forward to
            next_prefix = dest_location >> (b * (lvl - 1))
            if lvl == 2:
              next_bits = next_prefix & ((2 ** (b+1)) - 1)
            else:
              next_bits = next_prefix & ((2 ** b) - 1)
            log.info("routing downwards, next bits: %s" % bin(next_bits))

            neighbor_ips = self.get_neighbor_ip_map()
            valid_neighbors = [(k,v) for k,v in neighbor_ips.items() if (location(ip_to_val(v)) >> (b * (lvl - 1))) == next_prefix]
            invalid_ports = []
            pre_invalid_ports = [] # this is for stats; checking to see if we're sending a packet to a switch that's failed but no notification yet
            for k,v in valid_neighbors:
              if k in self.dead_switches:
                port = self.TOPO['outport_mappings'][(self.graph_name, k)]
                invalid_ports.append(port)
              elif k in self.pre_dead_switches:
                port = self.TOPO['outport_mappings'][(self.graph_name, k)]
                pre_invalid_ports.append(port)

            # PUSHBACK: add to invalid ports if we've gotten a pushback message
            for failed_prefix, message in self.pb_messages.items():
                fail_lvl = message['failed_level']
                if (dest_location >> (b * fail_lvl)) == failed_prefix:
                    log.info("    PUSHBACK: can't route DOWN through %s" % (message['from_switch'],))
                    invalid_ports.append(self.TOPO['outport_mappings'][(self.graph_name, message['from_switch'])]) 

            # all neighbors that fit the IP value match are actually dead
            if len(valid_neighbors) == len(invalid_ports):
              log.info("no valid switches")
              valid_neighbors = neighbor_ips.items()

            for k, v in valid_neighbors:
              out_port = self.TOPO['outport_mappings'][(self.graph_name, k)]
              if out_port == event.port or out_port in invalid_ports:
                # log.info("hello my name is DOWN-TINGU and i am not sending out of port "  + str(out_port))
                continue

              if out_port in pre_invalid_ports:
                log.info("[STATS] sending to switch that's already down (no notification yet)")

              # log.info("routing down to switch %s out of port %s" % (k, out_port))
              self.resend_packet(packet_in, out_port)
              break


      else: # route upwards
        log.info("routing upwards from level %d to level %d" % (lvl, lvl + 1))

        neighbor_ips = self.get_neighbor_ip_map()

        upper_level = [(k,v) for k,v in neighbor_ips.items() if level(ip_to_val(v)) == lvl + 1]
        invalid_ports = []
        for k,v in upper_level:
          if k in self.dead_switches:
            port = self.TOPO['outport_mappings'][(self.graph_name, k)]
            invalid_ports.append(port)

        # PUSHBACK: add to invalid ports if we've gotten a pushback message
        for failed_prefix, message in self.pb_messages.items():
            fail_lvl = message['failed_level']
            if dest_location >> (b * fail_lvl) == failed_prefix:
                log.info("    PUSHBACK: can't route UP through %s" % (message['from_switch'],))
                invalid_ports.append(self.TOPO['outport_mappings'][(self.graph_name, message['from_switch'])]) 

        if len(invalid_ports) == len(upper_level):
          log.info("no valid switches")
          upper_level = neighbor_ips.items()

        while True:
          random_switch = random.choice(upper_level)[0]

          out_port = self.TOPO['outport_mappings'][(self.graph_name, random_switch)]
          if out_port != event.port and out_port not in invalid_ports:
              break
          # log.info("hello my name is UP-TINGU and i am not sending out of port "  + str(out_port))
        # log.info("routing up to switch %s out of port %s" % (random_switch, out_port))

        self.resend_packet(packet_in, out_port)


def launch (p):
    
  topo = pickle.load(open(p))
  log.info(topo)

  def start_switch (event):
    log.info("Controlling %s" % (event.connection,))
    log.info("DPID is "  + str(event.dpid))
    switch = TopoSwitch(event.connection, event.dpid, topo)
    
    if not core.hasComponent("list"):
      s = SwitchList()
      core.register("list", s)
    core.list.add(switch)

  core.openflow.addListenerByName("ConnectionUp", start_switch)
  #core.openflow.addListenerByName("ConnectionDown", kill_switch)
