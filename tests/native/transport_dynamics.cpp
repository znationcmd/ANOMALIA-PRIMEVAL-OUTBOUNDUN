#include "../../unreal/Source/AnomaliaPrimeval/Vehicles/AnomaliaTransportDynamics.h"
#include <cassert>
#include <limits>
#include <iostream>
using namespace AnomaliaTransport;
int main()
{
    const double Dt=1.0/120;
    Settings P;
    Controls I;
    const Vector F{1,0,0},U{0,0,1};
    // A stopped aircraft falls, including with throttle: take-off requires airspeed.
    auto A=Acceleration(Mode::Plane,{},F,U,I,P,false,false,0);
    assert(A.Z==-980);
    A=Acceleration(Mode::Plane,{P.StallSpeed,0,0},F,U,I,P,false,false,0);
    assert(std::abs(A.Z)<1e-6);
    // An inverted wing pushes down rather than holding the airplane magically level.
    A=Acceleration(Mode::Plane,{P.StallSpeed,0,0},F,{0,0,-1},I,P,false,false,0);
    assert(A.Z < -1900);
    // Rotorcraft holds altitude only with power, and can climb and descend.
    assert(std::abs(Acceleration(Mode::Helicopter,{},F,U,I,P,true,false,0).Z)<1e-6);
    I.Vertical=1;
    assert(Acceleration(Mode::Helicopter,{},F,U,I,P,true,false,0).Z>0);
    I.Vertical=-1;
    assert(Acceleration(Mode::Helicopter,{},F,U,I,P,true,false,0).Z<0);
    assert(Acceleration(Mode::Helicopter,{},F,U,I,P,false,false,0).Z==-980);
    // Floatation converges after a disturbance instead of gaining energy forever.
    I={}; Vector V{}; double Height=150;
    for(int N=0;N<3600;++N)
    {
        A=Acceleration(Mode::Surface,V,F,U,I,P,false,true,-Height);
        V=Integrate(V,A,Dt,P.MaxSpeed); Height+=V.Z*Dt;
    }
    assert(std::abs(Height)<0.1 && std::abs(V.Z)<0.1);
    I.Throttle=1;
    assert(Acceleration(Mode::Surface,{},F,U,I,P,true,false,0).X==0);
    assert(Acceleration(Mode::Surface,{},F,U,I,P,true,false,0).Z==-980);
    // Dive controls work only with engine power and cannot reverse due to NaN input.
    I.Vertical=-1;
    assert(Acceleration(Mode::Submarine,{},F,U,I,P,true,true,0).Z<0);
    assert(Acceleration(Mode::Submarine,{},F,U,I,P,false,true,0).Z==0);
    I.Throttle=std::numeric_limits<double>::quiet_NaN();I.Vertical=std::numeric_limits<double>::infinity();
    I.Sanitize();assert(I.Throttle==0&&I.Vertical==0);
    // Long acceleration remains speed-limited; emergency braking cannot reverse the train.
    I={};I.Throttle=1;double Speed=0;
    for(int N=0;N<72000;++N) Speed=RailSpeed(Speed,I,P,true,Dt);
    assert(Speed<=P.MaxSpeed&&Speed>P.MaxSpeed*0.9);
    I.Throttle=0;I.Brake=1;
    for(int N=0;N<3600;++N) { Speed=RailSpeed(Speed,I,P,false,Dt);assert(Speed>=0); }
    assert(Speed==0);
    bool End=false;
    assert(RailDistance(990,30,1000,false,End)==1000&&End);
    assert(RailDistance(5,-20,1000,false,End)==0&&End);
    assert(RailDistance(990,30,1000,true,End)==20&&!End);
    assert(RailDistance(5,-20,1000,true,End)==985&&!End);
    assert(RailDistance(0,0,0,true,End)==0&&End);
    auto Invalid=Integrate({1,2,3},{4,5,6},100,P.MaxSpeed);
    assert(Invalid.Dot(Invalid)==0);
    P.MaxSpeed=std::numeric_limits<double>::infinity();assert(!P.Valid());
    std::cout<<"Transport numerical scenarios passed\n";
}
