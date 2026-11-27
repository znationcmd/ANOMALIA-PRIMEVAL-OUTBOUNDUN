#include "World/AnomaliaZPrigimaliaArchipelagoHeight.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <queue>
#include <vector>

using namespace AnomaliaZPrigimaliaArchipelago;
int main() {
 constexpr int N=480;
 constexpr double Grid=100.0;
 std::vector<std::uint8_t> land(N*N,0);
 std::vector<std::uint8_t> visited(N*N,0);
 for(int y=0;y<N;++y)for(int x=0;x<N;++x){
  const double east=-24000.0+(x+.5)*Grid;
  const double north=-24000.0+(y+.5)*Grid;
  land[y*N+x]=CoastDistance(east,north)>0.0 ? 1 : 0;
 }
 std::vector<double> components;
 for(int pos=0;pos<N*N;++pos){
  if(!land[pos]||visited[pos])continue;
  std::queue<int> q;q.push(pos);visited[pos]=1;
  std::uint32_t size=0;
  while(!q.empty()){
   const int a=q.front();q.pop();++size;
   const int ix=a%N,iy=a/N;
   for(const auto [dx,dy]:std::array<std::array<int,2>,4>{{{{1,0}},{{-1,0}},{{0,1}},{{0,-1}}}}){
    const int nx=ix+dx,ny=iy+dy;
    if(nx<0||nx>=N||ny<0||ny>=N)continue;
    const int v=ny*N+nx;
    if(land[v]&&!visited[v]){visited[v]=1;q.push(v);}
   }
  }
  components.push_back(size*.01); // each source-derived 100m cell is .01 km2
 }
 std::sort(components.begin(),components.end(),std::greater<double>());
 if(components.size()!=8 || components[0]<500.0){
  std::cerr<<"SKARVIK_ISLAND_LANDMASS_COUNT_BAD="<<components.size()<<'\n';return 2;
 }
 for(std::size_t i=1;i<components.size();++i)if(components[i]<5.0){
  std::cerr<<"SKARVIK_ISLAND_AREA_TOO_SMALL="<<components[i]<<'\n';return 3;
 }
 // Native source positions of the 14 pre-existing island settlements, plus
 // one provisional 7th-island harbor. All need original-coast dry land.
 const std::array<std::array<double,2>,15> centers = {{
  {{18000,-13000}},{{18590,-8890}},{{14000,15000}},{{16630,12620}},
  {{15700,11200}},{{-14000,17000}},{{-17000,17000}},
  {{-19090,18050}},{{-17870,19080}},{{-3000,-19000}},
  {{7000,19000}},{{-18350,-14870}},{{-18950,-13470}},
  {{-19570,-12710}},{{7620,-19080}}
 }};
 for(const auto& p:centers)if(CoastDistance(p[0],p[1])<=0){
  std::cerr<<"SKARVIK_EXISTING_ISLAND_TOWN_IN_SEA="<<p[0]<<","<<p[1]<<'\n';
  return 4;
 }
 std::cout<<"SKARVIK_NATIVE_SOURCE_SEVEN_DETACHED_ISLANDS_CONFIRMED=true\n"
          <<"SKARVIK_NATIVE_SOURCE_DRY_ISLAND_LOCALITY_CENTERS=15\n"
          <<"SKARVIK_NATIVE_SOURCE_TERRAIN_WORLD_CREATED=false\n"
          <<"SKARVIK_NATIVE_SOURCE_ISLANDS_KM2=";
 for(std::size_t i=1;i<components.size();++i)
  std::cout<<(i==1?"":",")<<components[i];
 std::cout<<'\n';
 return 0;
}
