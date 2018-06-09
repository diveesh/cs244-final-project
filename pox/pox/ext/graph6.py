import argparse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate F10 tops.")
    parser.add_argument('normal_csv', help='TCP cwnd trace for run with no failing switch')
    parser.add_argument('fail_csv', help='TCP cwnd trace for run with a failing switch')
    parser.add_argument('out', help='Output image path', default='fig6.eps')
    parser.add_argument('--fail_time', help='Moment in trace where switch failed', default=15, type=int)
    args = parser.parse_args()

    # columns: timestamp, src_ip, dest_ip, cwnd
    normalx, normaly = [], []
    with open(args.normal_csv, 'r') as f:
        for i, l in enumerate(f.readlines()[1:]):
            s = l.split(',')
            if i == 0:
                first_timestamp = float(s[0])
            normalx.append(float(s[0]) - first_timestamp)
            normaly.append(int(s[3]))
    
    failx, faily = [], []
    with open(args.fail_csv, 'r') as f:
        for i, l in enumerate(f.readlines()[1:]):
            s = l.split(',')
            if i == 0:
                first_timestamp = float(s[0])
            failx.append(float(s[0]) - first_timestamp)
            faily.append(int(s[3]))

    plt.title("F10 - Figure 8")
    plt.xlabel("time (s)")
    plt.ylabel("Congestion Window")
    plt.figure(figsize=(15, 7))
    plt.plot(normalx, normaly, c='blue', linestyle='dotted', label="Without Failure")
    plt.plot(failx, faily, c='red', label="With Failure")
    plt.legend(loc=3)
    plt.axvline(x=args.fail_time, c='black', linestyle='dashed')
    plt.savefig(args.out, format="eps", dpi=1000)

