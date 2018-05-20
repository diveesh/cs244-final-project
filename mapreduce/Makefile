GO := GOPATH="$(PWD)" go

# Recursive wildcard. Usage: $(call rwildcard,dir/,*.c)
rwildcard=$(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))

LIB_FILES := $(call rwildcard,src/mapreduce/,*.go)

all: wordcount invertedindex

wordcount: $(call rwildcard,src/wordcount/,*.go) $(LIB_FILES)
	$(GO) build wordcount

invertedindex: $(call rwildcard,src/invertedindex/,*.go) $(LIB_FILES)
	$(GO) build invertedindex

clean:
	rm -f wordcount invertedindex 
	rm -f data/output/mr*
