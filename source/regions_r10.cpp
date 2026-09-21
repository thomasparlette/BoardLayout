#include <vector>
#include <cstdint>
#include <iostream>
using namespace std;
int main(){uint32_t W,H;cin.read((char*)&W,4);cin.read((char*)&H,4);uint32_t N=W*H,M=8*N;vector<uint8_t>b(M),v(N);vector<uint32_t>lab(M,0),q;cin.read((char*)b.data(),M);cin.read((char*)v.data(),N);q.reserve(M);uint32_t count=0;for(uint32_t seed=0;seed<M;seed++){if(b[seed]||lab[seed])continue;++count;q.clear();q.push_back(seed);lab[seed]=count;for(size_t i=0;i<q.size();i++){auto n=q[i],a=n%N,x=a%W,y=a/W,l=n/N;auto push=[&](uint32_t z){if(!b[z]&&!lab[z]){lab[z]=count;q.push_back(z);}};if(x)push(n-1);if(x+1<W)push(n+1);if(y)push(n-W);if(y+1<H)push(n+W);if(x&&y)push(n-W-1);if(x+1<W&&y)push(n-W+1);if(x&&y+1<H)push(n+W-1);if(x+1<W&&y+1<H)push(n+W+1);if(v[a])for(uint32_t j=0;j<8;j++)if(j!=l)push(j*N+a);}}cerr<<"WIDE COMPONENTS "<<count<<"\n";cout.write((char*)lab.data(),M*4);}
