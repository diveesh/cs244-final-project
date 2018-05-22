package mapreduce

import (
	"fmt"
	"log"
	// "math/rand"
	"net"
	"net/rpc"
	"os"
	//	"runtime"
)

var RPCProtocol string

func init() {
	RPCProtocol = "tcp"
}

func startRPCServer(address string, rcvr interface{}) (*rpc.Server, net.Listener) {
	rpcServer := rpc.NewServer()
	rpcServer.Register(rcvr)

	if RPCProtocol == "unix" {
		os.Remove(address)
	}

	l, e := net.Listen(RPCProtocol, address)
	if e != nil {
		log.Fatalf("Listen error on %s: %v\n", address, e)
	}

	return rpcServer, l
}

func serverLoop(server *rpc.Server, l net.Listener, isActive func() bool) {
	for isActive() {
		conn, err := l.Accept()
		if err != nil {
			continue
		}

		go func() {
			server.ServeConn(conn)
			conn.Close()
		}()
	}

	fmt.Println("RPC server is done.")
}

func startMasterRPCServer(mr *ParallelMaster) net.Listener {
	fmt.Printf("Starting master rpc server on %s...\n", mr.addr)
	server, listener := startRPCServer(mr.addr, &RPCMaster{mr})
	go func() {
		serverLoop(server, listener, mr.IsActive)
		mr.done <- true
	}()

	return listener
}

func startWorkerRPCServer(w *Worker) net.Listener {
	server, listener := startRPCServer(w.address, (*RPCWorker)(w))
	go func() {
		serverLoop(server, listener, w.IsActive)
		w.done <- true
	}()

	return listener
}

func call(address, name string, args interface{}, reply interface{}) bool {
	c, errx := rpc.Dial(RPCProtocol, address)
	if errx != nil {
		return false
	}

	defer c.Close()
	err := c.Call(name, args, reply)
	if err == nil {
		return true
	}

	fmt.Println(err)
	return false
}

// Invokes the task named `name` on the worker at address `worker` with the
// arguments `args`. The workers response, if any, is written to `reply`. Blocks
// until the worker responds or the connection fails. Returns `true` if the
// worker responded and `false` if the connection failed.
func callWorker(worker, name string, args interface{}, reply interface{}) bool {
	return call(worker, "RPCWorker."+name, args, reply)
}

func callMaster(addr string, name string, args interface{}, reply interface{}) bool {
	return call(addr, "RPCMaster."+name, args, reply)
}
