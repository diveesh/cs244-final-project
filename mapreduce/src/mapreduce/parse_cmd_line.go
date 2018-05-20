package mapreduce

import (
	"flag"
	"fmt"
	"os"
)

type NodeType int

const (
	ParallelMasterNode NodeType = iota
	WorkerNode
)

// Creates a new node type. Exactly one of seq, parallel, or worker has to be
// true.
func NewNodeType(parallel, worker bool) NodeType {
	if parallel {
		return ParallelMasterNode
	} else {
		return WorkerNode
	}
}

// Returns a string representation of the NodeType.
func (t NodeType) String() string {
	switch t {
	case ParallelMasterNode:
		return "ParallelMaster"
	case WorkerNode:
		return "Worker"
	}

	return "Unknown"
}

// Prints the usage information and exits.
func usageAndExit() {
	binName := os.Args[0]
	fmt.Printf("Usage: %s [-p, -r <reducers>, -w, -a <workerAddress:Port>, -m <masterAddress:Port>] <inputFile1, "+
		"inputFile2, ...>\n", binName)

	flag.PrintDefaults()
	os.Exit(1)
}

// Print the error string 'msg', then prints the usage information, then exits.
func msgUsageAndExit(msg string) {
	fmt.Printf("Error: %s\n\n", msg)
	usageAndExit()
}

// Parses the command line for MapReduce programs. Returns a tuple containing
// whether the sequential flag (-s), parallel flag (-p), or worker flag (-w) was
// set, the number of reduce workers requested (-r [numReducers]), and a slice
// of vetted (existing, regular) input filenames. If passed in files or the
// parameters are invalid, this function terminates the program and prints an
// error and usage message.
func ParseCmdLine() (NodeType, uint, string, string, []string) {
	parallel := flag.Bool("p", false, "whether this is a parallel master")
	worker := flag.Bool("w", false, "whether this is a worker node")
	reducers := flag.Uint("r", 20, "number of `reducers` - only used by masters")
	masterAddr := flag.String("m", "localhost:7782", "ip:port of master node")
	workerAddr := flag.String("a", "localhost:7783", "ip:port of worker node, if worker")
	flag.Parse()

	if !*worker && !*parallel {
		msgUsageAndExit("Must specify if node is `parallel master` or `worker`.")
	}

	inputFileNames := flag.Args()
	if *parallel && len(inputFileNames) < 1 {
		msgUsageAndExit("Need at least one input file for master.")
	}

	for _, fileName := range inputFileNames {
		if st, err := os.Stat(fileName); err == nil {
			if !st.Mode().IsRegular() {
				msg := fmt.Sprintf("'%s' is not a regular file.", fileName)
				msgUsageAndExit(msg)
			}
		} else {
			msg := fmt.Sprintf("'%s' does not exist.", fileName)
			msgUsageAndExit(msg)
		}
	}

	nodeType := NewNodeType(*parallel, *worker)
	return nodeType, *reducers, *masterAddr, *workerAddr, inputFileNames
}

// Starts a node using the mapF and reduceF functions. Starting a node means:
// 1) Parsing the command line arguments to see what kind of node this is.
// 2) Starting the appropriate communication channels.
func Run(jobName string, mapF MapFunction, reduceF ReduceFunction) {
	nodeType, reducers, masterAddr, workerAddr, inputFileNames := ParseCmdLine()
	switch nodeType {
	case WorkerNode:
		worker := NewWorker(jobName, mapF, reduceF, masterAddr, workerAddr)
		worker.Start()
	case ParallelMasterNode:
		master := NewParallelMaster(jobName, inputFileNames, reducers, mapF,
			reduceF, masterAddr)
		master.Start()
		master.Merge()
	}
}
