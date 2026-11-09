// ======================================================================
// \title  FlightComputer.cpp
// AI-assisted Asteria implementation; based on the official F Prime template.
// \brief  cpp file for FlightComputer component implementation class
// ======================================================================

#include "Asteria/Components/FlightComputer/FlightComputer.hpp"

namespace Asteria {

// ----------------------------------------------------------------------
// Component construction and destruction
// ----------------------------------------------------------------------

FlightComputer::FlightComputer(const char *const compName)
    : FlightComputerComponentBase(compName) {}

FlightComputer::~FlightComputer() {}

// ----------------------------------------------------------------------
// Handler implementations for typed input ports
// ----------------------------------------------------------------------

void FlightComputer::run_handler(FwIndexType portNum, U32 context) {
  (void)portNum;
  (void)context;
  std::lock_guard<std::mutex> lock(modelMutex);
  auto previous = model.mode;
  lastResult = model.apply("STEP", 1);
  if (previous != model.mode && isConnected_logOut_OutputPort(0))
    log_ACTIVITY_HI_ModeChanged(static_cast<U32>(model.mode));
  publish();
}

// ----------------------------------------------------------------------
// Handler implementations for commands
// ----------------------------------------------------------------------

void FlightComputer::BOOT_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("BOOT", 0, opCode, cmdSeq);
}

void FlightComputer::SAFE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("SAFE", 0, opCode, cmdSeq);
}

void FlightComputer::RECOVER_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("RECOVER", 0, opCode, cmdSeq);
}

void FlightComputer::RESUME_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("RESUME", 0, opCode, cmdSeq);
}

void FlightComputer::PAYLOAD_ON_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("PAYLOAD_ON", 0, opCode, cmdSeq);
}

void FlightComputer::PAYLOAD_OFF_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("PAYLOAD_OFF", 0, opCode, cmdSeq);
}

void FlightComputer::HEATER_ON_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("HEATER_ON", 0, opCode, cmdSeq);
}

void FlightComputer::HEATER_OFF_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("HEATER_OFF", 0, opCode, cmdSeq);
}

void FlightComputer::ADCS_ON_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("ADCS_ON", 0, opCode, cmdSeq);
}

void FlightComputer::ADCS_OFF_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("ADCS_OFF", 0, opCode, cmdSeq);
}

void FlightComputer::POINT_cmdHandler(FwOpcodeType opCode, U32 cmdSeq,
                                      F64 value) {
  applyCommand("POINT", value, opCode, cmdSeq);
}

void FlightComputer::DESATURATE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("DESATURATE", 0, opCode, cmdSeq);
}

void FlightComputer::INJECT_FAULT_cmdHandler(FwOpcodeType opCode, U32 cmdSeq,
                                             F64 value) {
  applyCommand("INJECT_FAULT", value, opCode, cmdSeq);
}

void FlightComputer::CLEAR_FAULTS_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("CLEAR_FAULTS", 0, opCode, cmdSeq);
}

void FlightComputer::STEP_cmdHandler(FwOpcodeType opCode, U32 cmdSeq,
                                     F64 value) {
  applyCommand("STEP", value, opCode, cmdSeq);
}

void FlightComputer::SNAPSHOT_cmdHandler(FwOpcodeType opCode, U32 cmdSeq) {
  applyCommand("SNAPSHOT", 0, opCode, cmdSeq);
}

void FlightComputer::setSeed(U32 seed) {
  std::lock_guard<std::mutex> lock(modelMutex);
  model = asteria::Flight(seed);
}
std::string FlightComputer::snapshot() {
  std::lock_guard<std::mutex> lock(modelMutex);
  return model.json(lastResult);
}
void FlightComputer::applyCommand(const char *command, double value,
                                  FwOpcodeType opcode, U32 seq) {
  std::lock_guard<std::mutex> lock(modelMutex);
  const auto previous = model.mode;
  lastResult = model.apply(command, value);
  if (!lastResult.ok && isConnected_logOut_OutputPort(0))
    log_WARNING_HI_CommandRejected(opcode);
  if (previous != model.mode && isConnected_logOut_OutputPort(0))
    log_ACTIVITY_HI_ModeChanged(static_cast<U32>(model.mode));
  publish();
  if (isConnected_cmdResponseOut_OutputPort(0))
    cmdResponse_out(opcode, seq,
                    lastResult.ok ? Fw::CmdResponse::OK
                                  : Fw::CmdResponse::EXECUTION_ERROR);
}
void FlightComputer::publish() {
  if (!isConnected_tlmOut_OutputPort(0))
    return;
  tlmWrite_Time(static_cast<F64>(model.time));
  tlmWrite_BatterySoc(static_cast<F64>(model.eps.soc));
  tlmWrite_BusVoltage(static_cast<F64>(model.eps.voltage));
  tlmWrite_SolarPower(static_cast<F64>(model.eps.solar));
  tlmWrite_LoadPower(static_cast<F64>(model.eps.load));
  tlmWrite_Temperature(static_cast<F64>(model.thermal.temperature));
  tlmWrite_Heater(static_cast<F64>(model.thermal.heater));
  tlmWrite_Attitude(static_cast<F64>(model.adcs.angle));
  tlmWrite_AngularRate(static_cast<F64>(model.adcs.rate));
  tlmWrite_WheelRpm(static_cast<F64>(model.adcs.wheel));
  tlmWrite_TargetAngle(static_cast<F64>(model.adcs.target));
  tlmWrite_SensorAge(static_cast<F64>(model.adcs.sensorAge));
  tlmWrite_AdcsEnabled(static_cast<F64>(model.adcs.enabled));
  tlmWrite_LinkConnected(static_cast<F64>(model.comms.connected));
  tlmWrite_LinkAge(static_cast<F64>(model.comms.age));
  tlmWrite_Packets(static_cast<F64>(model.comms.packets));
  tlmWrite_PayloadEnabled(static_cast<F64>(model.payload.enabled));
  tlmWrite_PayloadData(static_cast<F64>(model.payload.data));
  tlmWrite_Ticks(static_cast<F64>(model.scheduler.ticks));
  tlmWrite_MissedDeadlines(static_cast<F64>(model.scheduler.missed));
  tlmWrite_CommandsAccepted(static_cast<F64>(model.accepted));
  tlmWrite_CommandsRejected(static_cast<F64>(model.rejected));
  tlmWrite_OrbitPhase(static_cast<F64>(std::fmod(model.time, 5400.0) / 5400.0));
  tlmWrite_Sunlight(static_cast<F64>(std::fmod(model.time, 5400.0) < 3500));
  tlmWrite_Healthy(static_cast<F64>(model.healthy()));
  tlmWrite_HealthyDwell(static_cast<F64>(model.time - model.healthySince));
  tlmWrite_Mode(static_cast<U32>(model.mode));
}
std::string FlightComputer::frameError(const char *reason) {
  std::lock_guard<std::mutex> lock(modelMutex);
  return model.json({false, reason});
}

void FlightComputer::execute(const std::string &command, double value) {
  static const std::array<const char *, 16> names = {
      "BOOT",         "SAFE",         "RECOVER",   "RESUME",
      "PAYLOAD_ON",   "PAYLOAD_OFF",  "HEATER_ON", "HEATER_OFF",
      "ADCS_ON",      "ADCS_OFF",     "POINT",     "DESATURATE",
      "INJECT_FAULT", "CLEAR_FAULTS", "STEP",      "SNAPSHOT"};
  auto found = std::find(names.begin(), names.end(), command);
  if (found == names.end() || !std::isfinite(value) ||
      (command != "POINT" && command != "STEP" && command != "INJECT_FAULT" &&
       value != 0)) {
    applyCommand(command.c_str(), value, 0, ++sequence);
    return;
  }
  Fw::CmdArgBuffer args;
  if (command == "POINT" || command == "STEP" || command == "INJECT_FAULT") {
    auto result = args.serializeFrom(static_cast<F64>(value));
    FW_ASSERT(result == Fw::FW_SERIALIZE_OK);
  }
  cmdIn_handlerBase(0, static_cast<FwOpcodeType>(found - names.begin()),
                    ++sequence, args);
}

} // namespace Asteria
