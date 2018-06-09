python main.py -s --out fig10result.eps
pushd ./pox/pox/ext
./run.sh
cp fig6*.eps ../../../
popd
