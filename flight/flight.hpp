#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

namespace asteria {
constexpr double pi = 3.14159265358979323846;
enum class Mode { BOOT, NOMINAL, SAFE, RECOVERY };
inline const char* name(Mode m) { return std::array<const char*,4>{"BOOT","NOMINAL","SAFE","RECOVERY"}[static_cast<int>(m)]; }
struct Event { double time; std::string code; std::string severity; };
struct EPS { double soc=82, voltage=7.9, solar=0, load=0; };
struct ADCS { double angle=0, rate=.12, wheel=0, target=0, sensorAge=0; bool enabled=true; };
struct Thermal { double temperature=22; bool heater=false; };
struct Comms { bool connected=true; double age=0; std::uint64_t packets=0; };
struct Payload { bool enabled=false; double data=0; };
struct Scheduler { std::uint64_t ticks=0, missed=0; };
struct Result { bool ok; std::string reason; };
class Flight {
public:
 EPS eps; ADCS adcs; Thermal thermal; Comms comms; Payload payload; Scheduler scheduler;
 Mode mode=Mode::BOOT;
 double time=0, safeSince=0, healthySince=0;
 std::uint32_t seed=42, rng=42;
 std::uint64_t accepted=0, rejected=0;
 std::array<bool,6> faults{};
 std::vector<Event> events;
 explicit Flight(std::uint32_t s=42):seed(s),rng(s?s:1) { event("BOOT","INFO"); }
 void event(const std::string& code,const std::string& severity="INFO") { events.push_back({time,code,severity}); if(events.size()>256) events.erase(events.begin()); }
 double noise() { rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5; return (double(rng)/4294967295.0-.5)*.002; }
 bool healthy() const { return eps.soc>=35 && thermal.temperature<45 && adcs.sensorAge<2 && std::abs(adcs.wheel)<5500 && comms.connected && std::none_of(faults.begin(),faults.end(),[](bool x){return x;}); }
 void setMode(Mode m) { if(mode!=m) {mode=m; event(std::string("MODE_")+name(m),m==Mode::SAFE?"CRITICAL":"INFO"); if(m==Mode::SAFE) safeSince=time;} if(m==Mode::SAFE||m==Mode::RECOVERY){payload.enabled=false;thermal.heater=false;} }
 void protect() {
  bool bad=eps.soc<20 || thermal.temperature>=50 || adcs.sensorAge>=3 || std::abs(adcs.wheel)>=6000 || faults[4] || comms.age>=15;
  if(bad){healthySince=time;setMode(Mode::SAFE);payload.enabled=false;thermal.heater=false;}
  if(!healthy()) healthySince=time;
 }
 void stepOne() {
  time+=1; ++scheduler.ticks;
  bool sun=std::fmod(time,5400.0)<3500;
  eps.solar=sun?12:0;
  eps.load=mode==Mode::SAFE?3:5;
  eps.load+=(payload.enabled?8:0)+(thermal.heater?4:0)+(adcs.enabled?1:0);
  eps.soc=std::clamp(eps.soc+(eps.solar-eps.load)/720.0,0.0,100.0);
  if(faults[0]) eps.soc=std::max(0.0,eps.soc-.25);
  eps.voltage=6.0+eps.soc*.024;
  thermal.temperature+=((sun?24.0:4.0)-thermal.temperature)/500.0+(payload.enabled?.012:0)+(thermal.heater?.025:0)+(faults[1]?.3:0);
  adcs.sensorAge=faults[2]?adcs.sensorAge+1:0;
  if(adcs.enabled&&!faults[2]) { double error=std::remainder(adcs.target-adcs.angle,360.0); double torque=std::clamp(error*.0006-adcs.rate*.05,-.02,.02); adcs.rate+=torque+noise(); adcs.wheel=std::clamp(adcs.wheel-torque*100,-6500.0,6500.0); }
  adcs.angle=std::remainder(adcs.angle+adcs.rate,360.0);
  if(faults[5]) adcs.wheel=6200;
  comms.connected=!faults[3]; comms.age=comms.connected?0:comms.age+1;
  if(comms.connected) ++comms.packets;
  if(faults[4]) ++scheduler.missed;
  if(payload.enabled) payload.data+=.25;
  protect();
 }
 Result apply(const std::string& cmd,double value=0) {
  auto fail=[&](const std::string& reason){++rejected;event("REJECT_"+cmd,"WARNING");return Result{false,reason};};
  if(!std::isfinite(value)) return fail("NONFINITE_PARAMETER");
  if(cmd!="POINT" && cmd!="STEP" && cmd!="INJECT_FAULT" && value!=0) return fail("UNEXPECTED_PARAMETER");
  if(!comms.connected && cmd!="STEP" && cmd!="CLEAR_FAULTS" && cmd!="INJECT_FAULT" && cmd!="SNAPSHOT") return fail("LINK_UNAVAILABLE");
  if(cmd=="SNAPSHOT") return {true,"TELEMETRY"};
  if(cmd=="STEP") { if(value<1||value>3600||std::floor(value)!=value) return fail("STEP_RANGE_1_3600"); for(int i=0;i<int(value);++i)stepOne(); return {true,"STEPPED"}; }
  if(cmd=="BOOT") { if(mode!=Mode::BOOT) return fail("INVALID_TRANSITION");setMode(Mode::NOMINAL); }
  else if(cmd=="SAFE") {setMode(Mode::SAFE);}
  else if(cmd=="RECOVER") {if(mode!=Mode::SAFE) return fail("INVALID_TRANSITION");if(!healthy()||time-healthySince<10) return fail("RECOVERY_GATE");setMode(Mode::RECOVERY);}
  else if(cmd=="RESUME") {if(mode!=Mode::RECOVERY) return fail("INVALID_TRANSITION");if(!healthy())return fail("RECOVERY_GATE");setMode(Mode::NOMINAL);}
  else if(cmd=="PAYLOAD_ON") {if(mode!=Mode::NOMINAL||eps.soc<40||thermal.temperature>=40||adcs.sensorAge>0||std::abs(adcs.rate)>.5) return fail("PAYLOAD_INTERLOCK");payload.enabled=true;}
  else if(cmd=="PAYLOAD_OFF") {payload.enabled=false;}
  else if(cmd=="HEATER_ON") {if(mode!=Mode::NOMINAL||eps.soc<30||thermal.temperature>=15)return fail("HEATER_INTERLOCK");thermal.heater=true;}
  else if(cmd=="HEATER_OFF") {thermal.heater=false;}
  else if(cmd=="ADCS_ON") {adcs.enabled=true;}
  else if(cmd=="ADCS_OFF") {if(payload.enabled)return fail("PAYLOAD_ACTIVE");adcs.enabled=false;}
  else if(cmd=="POINT") {if(mode!=Mode::NOMINAL||!adcs.enabled||adcs.sensorAge>0)return fail("POINT_INTERLOCK");if(value < -180||value > 180)return fail("ANGLE_RANGE");adcs.target=value;}
  else if(cmd=="DESATURATE") {if(payload.enabled)return fail("PAYLOAD_ACTIVE");if(faults[5])return fail("FAULT_ACTIVE");adcs.wheel=0;}
  else if(cmd=="INJECT_FAULT") {if(value<0||value>5||std::floor(value)!=value)return fail("FAULT_RANGE");faults[int(value)]=true;if(value==0)eps.soc=15;if(value==1)thermal.temperature=55;if(value==2)adcs.sensorAge=3;if(value==3){comms.connected=false;comms.age=0;}if(value==5)adcs.wheel=6200;event("FAULT_"+std::to_string(int(value)),"CRITICAL");protect();}
  else if(cmd=="CLEAR_FAULTS") {faults.fill(false);comms.connected=true;comms.age=0;adcs.sensorAge=0;event("FAULT_SOURCES_CLEARED");}
  else return fail("UNKNOWN_COMMAND");
  ++accepted;event("CMD_"+cmd);return {true,"ACKNOWLEDGED"};
 }
 std::string json(const Result& result) const {
  std::ostringstream o;o<<std::setprecision(12);
  o<<"{\"protocol_version\":1,\"ok\":"<<(result.ok?"true":"false")<<",\"reason\":\""<<result.reason<<"\",\"mode\":\""<<name(mode)<<"\",\"seed\":"<<seed<<",\"telemetry\":{";
  o<<"\"time\":"<<time<<",\"battery_soc\":"<<eps.soc<<",\"bus_voltage\":"<<eps.voltage<<",\"solar_power\":"<<eps.solar<<",\"load_power\":"<<eps.load<<",\"temperature\":"<<thermal.temperature<<",\"heater\":"<<thermal.heater<<",\"attitude\":"<<adcs.angle<<",\"angular_rate\":"<<adcs.rate<<",\"wheel_rpm\":"<<adcs.wheel<<",\"target_angle\":"<<adcs.target<<",\"sensor_age\":"<<adcs.sensorAge<<",\"adcs_enabled\":"<<adcs.enabled<<",\"link_connected\":"<<comms.connected<<",\"link_age\":"<<comms.age<<",\"packets\":"<<comms.packets<<",\"payload_enabled\":"<<payload.enabled<<",\"payload_data\":"<<payload.data<<",\"ticks\":"<<scheduler.ticks<<",\"missed_deadlines\":"<<scheduler.missed<<",\"commands_accepted\":"<<accepted<<",\"commands_rejected\":"<<rejected<<",\"orbit_phase\":"<<std::fmod(time,5400.0)/5400.0<<",\"sunlight\":"<<(std::fmod(time,5400.0)<3500)<<",\"healthy\":"<<healthy()<<",\"healthy_dwell\":"<<time-healthySince<<"},\"faults\":[";
  for(std::size_t i=0;i<faults.size();++i){if(i)o<<',';o<<(faults[i]?"true":"false");}
  o<<"],\"events\":[";
  for(std::size_t i=0;i<events.size();++i){if(i)o<<',';o<<"{\"time\":"<<events[i].time<<",\"code\":\""<<events[i].code<<"\",\"severity\":\""<<events[i].severity<<"\"}";}
  return o.str()+"]}";
 }
};
}
