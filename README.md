# F10 Reproduction
### CS244 Final Project (Spring 2018)

Diveesh Singh and Jean-Luc Watson

Reproduces Figures 6 and 10 from the F10 NSDI paper located [here](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final215.pdf).

#### [Final Report (coming soon)]()

#### Instructions

  1. Start a Google Compute instance. We used these specs:

  ```
  1 vCPU with 3.75 GB memory
  Ubuntu 16.04 LTS // Ubuntu is very important
  us-west1-a 
  ```

  2. Install git (`sudo apt install git`) and clone this repository:

  ```
  $ git clone https://github.com/diveesh/cs244-final-project
  ```

  3. Set up the project:

  ```
  $ cd cs244-final-project
  $ ./setup_project.sh
  ```

  You will need to affirm `Y` for various package installations. The script will install Mininet 2.2.2 from source, as well as `networkx`, `matplotlib`, `simplejson`, and `iperf3`.

  4. Re-generate the results:

  ```
  $ sudo ./main.sh
  ```

  The resulting .eps figure image files should appear in the top-level directory.

#### Other

The "full" path inflation (Figure 10) statistics for a complete 24-port AB FatTree topology take quite a long time to generate (~2 hours). The instructions above run a smaller version of the topology, but if you're interested in the complete version and you have some extra time, run the following command:

```
$ sudo python main.py -b --out large_fig10.eps
```

You can also try out a sample MapReduce application running on our topology (code gratefully sourced from David Maziere's CS240 _last_ spring, where we implemented MapReduce on top of a socket interface). Here are the instructions for that:

```
$ pwd
~/cs244-final-project
$ cd pox/pox/ext/
$ TODO
```

