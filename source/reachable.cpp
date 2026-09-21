#include <vector>
#include <cstdint>
#include <iostream>
using namespace std;
int main(){uint32_t W,H;cin.read((char*)&W,4);cin.read((char*)&H,4);uint32_t N=W*H,M=8*N;vector<uint8_t>b(M),v(N),seen(M,0),out(M,0);cin.read((char*)b.data(),M);cin.read((char*)v.data(),N);vector<uint32_t>q,best;q.reserve(M);for(uint32_t seed=0;seed<M;seed++){if(b[seed]||seen[seed])continue;q.clear();q.push_back(seed);seen[seed]=1;for(size_t i=0;i<q.size();i++){auto n=q[i],a=n%N,x=a%W,y=a/W,l=n/N;auto push=[&](uint32_t z){if(!b[z]&&!seen[z]){seen[z]=1;q.push_back(z);}};if(x)push(n-1);if(x+1<W)push(n+1);if(y)push(n-W);if(y+1<H)push(n+W);if(v[a])for(uint32_t j=0;j<8;j++)if(j!=l)push(j*N+a);}if(q.size()>best.size())best=q;}for(auto n:best)out[n]=1;cerr<<"WIDE REGION "<<best.size()<<" cells\n";cout.write((char*)out.data(),M);}
