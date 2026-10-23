#pragma once
// Engine-independent numerical kernel; centimetres, seconds. Not a certified flight/naval simulator.
#include <algorithm>
#include <cmath>

namespace AnomaliaTransport
{
enum class Mode { Plane, Helicopter, Surface, Submarine, Rail };
inline double Axis(double V) { return std::isfinite(V) ? std::clamp(V, -1.0, 1.0) : 0.0; }
struct Vector
{
    double X=0, Y=0, Z=0;
    Vector operator+(Vector B) const { return {X+B.X,Y+B.Y,Z+B.Z}; }
    Vector operator*(double K) const { return {X*K,Y*K,Z*K}; }
    double Dot(Vector B) const { return X*B.X+Y*B.Y+Z*B.Z; }
    bool Finite() const { return std::isfinite(X)&&std::isfinite(Y)&&std::isfinite(Z); }
};
struct Controls
{
    double Throttle=0, Yaw=0, Pitch=0, Roll=0, Vertical=0, Brake=0;
    void Sanitize()
    {
        Throttle=Axis(Throttle); Yaw=Axis(Yaw); Pitch=Axis(Pitch);
        Roll=Axis(Roll); Vertical=Axis(Vertical); Brake=std::max(0.0,Axis(Brake));
    }
};
struct Settings
{
    double MaxSpeed=8000, Acceleration=600, Drag=0.18, StallSpeed=3500;
    double HoverAcceleration=980, WaterSpring=2.5, WaterDamping=3.2, DiveSpeed=500;
    bool Valid() const
    {
        return std::isfinite(MaxSpeed)&&MaxSpeed>0 && std::isfinite(Acceleration)&&Acceleration>0 &&
          std::isfinite(Drag)&&Drag>=0 && std::isfinite(StallSpeed)&&StallSpeed>0 &&
          std::isfinite(HoverAcceleration)&&HoverAcceleration>=0 &&
          std::isfinite(WaterSpring)&&WaterSpring>=0 && std::isfinite(WaterDamping)&&WaterDamping>=0 &&
          std::isfinite(DiveSpeed)&&DiveSpeed>0;
    }
};
// World basis is supplied by Unreal, so bank and pitch affect thrust and lift.
inline Vector Acceleration(Mode Kind, Vector Velocity, Vector Forward, Vector Up,
    Controls Input, const Settings& P, bool Powered, bool InWater, double SurfaceError)
{
    Input.Sanitize();
    if (!P.Valid() || !Velocity.Finite() || !Forward.Finite() || !Up.Finite() || !std::isfinite(SurfaceError)) return {};
    const double Thrust=Powered?Input.Throttle:0;
    const double Speed=std::max(0.0,Velocity.Dot(Forward));
    const double Drag=P.Drag+Input.Brake*1.8;
    Vector A=Velocity*(-Drag);
    switch(Kind)
    {
    case Mode::Plane:
    {
        // Lift scales with airspeed; stopped/unpowered aircraft cannot hover.
        const double Lift=980*std::clamp(Speed*Speed/(P.StallSpeed*P.StallSpeed),0.0,2.0);
        A=A+Forward*(std::max(0.0,Thrust)*P.Acceleration)+Up*Lift+Vector{0,0,-980};
        break;
    }
    case Mode::Helicopter:
        A=A+Forward*(Thrust*P.Acceleration)+Vector{0,0,-980};
        if(Powered) A=A+Up*(P.HoverAcceleration*(1.0+Input.Vertical*0.8));
        break;
    case Mode::Surface:
        if(InWater) A=A+Forward*(Thrust*P.Acceleration)+Vector{0,0,SurfaceError*P.WaterSpring-Velocity.Z*P.WaterDamping};
        else A=A+Vector{0,0,-980};
        break;
    case Mode::Submarine:
        if(InWater) A=A+Forward*(Thrust*P.Acceleration)+Vector{0,0,((Powered?Input.Vertical:0)*P.DiveSpeed-Velocity.Z)*1.5};
        else A=A+Vector{0,0,-980};
        break;
    case Mode::Rail: break; // Rail uses a scalar speed and never free-flight steering.
    }
    return A;
}
inline Vector Integrate(Vector Velocity, Vector A, double Dt, double MaxSpeed)
{
    if(!Velocity.Finite()||!A.Finite()||!std::isfinite(Dt)||Dt<=0||Dt>0.05||!std::isfinite(MaxSpeed)||MaxSpeed<=0) return {};
    Vector Next=Velocity+A*Dt;
    const double Length=std::sqrt(Next.Dot(Next));
    if(Length>MaxSpeed) Next=Next*(MaxSpeed/Length);
    return Next;
}
inline double RailSpeed(double Speed, Controls Input, const Settings& P, bool Powered, double Dt, double ReverseSpeedFraction=0.25)
{
    if(!std::isfinite(ReverseSpeedFraction)||ReverseSpeedFraction<0||ReverseSpeedFraction>1) return 0;
    if(!std::isfinite(Speed)||!std::isfinite(Dt)||Dt<=0||Dt>0.05||!P.Valid()) return 0;
    Input.Sanitize();
    Speed+=(Powered?Input.Throttle:0)*P.Acceleration*Dt;
    const double Deceleration=(Input.Brake*1200+30)*Dt;
    Speed=std::copysign(std::max(0.0,std::abs(Speed)-Deceleration),Speed);
    return std::clamp(Speed,-P.MaxSpeed*ReverseSpeedFraction,P.MaxSpeed);
}
inline double RailDistance(double Distance,double Delta,double Length,bool Loop,bool& AtEnd)
{
    AtEnd=true;
    if(!std::isfinite(Distance)||!std::isfinite(Delta)||!std::isfinite(Length)||Length<=0) return 0;
    const double Next=Distance+Delta;
    if(Loop) { AtEnd=false; return std::fmod(std::fmod(Next,Length)+Length,Length); }
    AtEnd=Next<0||Next>Length;
    return std::clamp(Next,0.0,Length);
}
}
