#include <vector>
#include <queue>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <algorithm>
#include <chrono>
using namespace std;
struct Entry{float f,g;uint32_t n;bool operator<(const Entry&o)const{return f==o.f?g<o.g:f>o.f;}};
template<class T>void readv(T&x){cin.read((char*)&x,sizeof(x));}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);
 uint32_t W,H,S,G;readv(W);readv(H);readv(S);readv(G);uint32_t N=W*H,M=N*8;
 vector<uint8_t> blocked(M),via(N),target(M,0),closed(M,0);cin.read((char*)blocked.data(),M);cin.read((char*)via.data(),N);
 vector<uint8_t>soft(M),vsoft(N);cin.read((char*)soft.data(),M);cin.read((char*)vsoft.data(),N);
 vector<uint32_t>starts(S),goals(G);cin.read((char*)starts.data(),S*4);cin.read((char*)goals.data(),G*4);
 float gx=0,gy=0;for(auto n:goals){target[n]=1;gx+=(n%N)%W;gy+=(n%N)/W;}gx/=G;gy/=G;
 auto heuristic=[&](uint32_t n){return max(0.f,abs(float(n%N%W)-gx)+abs(float(n%N/W)-gy)-30);};
 vector<float>dist(M,1e30f);vector<uint32_t>prev(M,UINT32_MAX);priority_queue<Entry>q;
 for(auto n:starts){dist[n]=0;q.push({heuristic(n),0,n});}
 auto start=chrono::steady_clock::now();uint32_t visits=0,end=UINT32_MAX;
 while(!q.empty()){
  auto a=q.top();q.pop();auto n=a.n;if(closed[n])continue;if(target[n]){end=n;break;}closed[n]=1;
  if((++visits%16384)==0 && chrono::duration<double>(chrono::steady_clock::now()-start).count()>8)break;
  uint32_t local=n%N,x=local%W,y=local/W,l=n/N;
  auto push=[&](uint32_t next,float cost){if(blocked[next]||closed[next])return;float g=a.g+cost+soft[next];if(g<dist[next]){dist[next]=g;prev[next]=n;q.push({g+1.05f*heuristic(next),g,next});}};
  if(x>0)push(n-1,1);if(x<W-1)push(n+1,1);if(y>0)push(n-W,1);if(y<H-1)push(n+W,1);
  if(x>0&&y>0)push(n-W-1,1.414214f);if(x<W-1&&y>0)push(n-W+1,1.414214f);
  if(x>0&&y<H-1)push(n+W-1,1.414214f);if(x<W-1&&y<H-1)push(n+W+1,1.414214f);
  if(via[local])for(uint32_t ll=0;ll<8;ll++)if(ll!=l)push(ll*N+local,70+3*vsoft[local]);
 }
 cerr<<"SEARCH visited="<<visits<<" queue="<<q.size()<<" starts="<<S<<" goals="<<G<<" success="<<(end!=UINT32_MAX)<<" seconds="<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<"\n";vector<uint32_t>path;if(end!=UINT32_MAX)for(auto n=end;n!=UINT32_MAX;n=prev[n])path.push_back(n);reverse(path.begin(),path.end());
 uint32_t size=path.size();cout.write((char*)&size,4);if(size)cout.write((char*)path.data(),4*size);
}
