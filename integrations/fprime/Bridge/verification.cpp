#include "Asteria/Components/FlightComputer/FlightComputer.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
class Sink : public Fw::PassiveComponentBase {
public:
  Sink() : Fw::PassiveComponentBase("verification") {}
  std::array<double, 27> values{};
  unsigned samples = 0, acknowledgments = 0;
  U32 lastSequence = 0;
  Fw::CmdResponse lastResponse = Fw::CmdResponse::OK;
  static void telemetry(Fw::PassiveComponentBase *base, FwIndexType,
                        FwChanIdType id, Fw::Time &, Fw::TlmBuffer &data) {
    auto &self = *static_cast<Sink *>(base);
    if (id >= 27)
      throw std::runtime_error("channel outside dictionary");
    data.resetDeser();
    if (id == 26) {
      U32 value = 0;
      if (data.deserializeTo(value) != Fw::FW_SERIALIZE_OK)
        throw std::runtime_error("mode decode");
      self.values[id] = value;
    } else {
      F64 value = 0;
      if (data.deserializeTo(value) != Fw::FW_SERIALIZE_OK)
        throw std::runtime_error("channel decode");
      self.values[id] = value;
    }
    ++self.samples;
  }
  static void response(Fw::PassiveComponentBase *base, FwIndexType,
                       FwOpcodeType, U32 sequence,
                       const Fw::CmdResponse &response) {
    auto &self = *static_cast<Sink *>(base);
    self.lastSequence = sequence;
    self.lastResponse = response;
    ++self.acknowledgments;
  }
};
void require(bool condition, const char *message) {
  if (!condition)
    throw std::runtime_error(message);
}
int main() {
  Asteria::FlightComputer computer("flightComputer");
  computer.init(0);
  Sink sink;
  Fw::InputTlmPort telemetry;
  telemetry.init();
  telemetry.addCallComp(&sink, Sink::telemetry);
  Fw::InputCmdResponsePort response;
  response.init();
  response.addCallComp(&sink, Sink::response);
  computer.set_tlmOut_OutputPort(0, &telemetry);
  computer.set_cmdResponseOut_OutputPort(0, &response);
  computer.execute("BOOT", 0);
  require(sink.acknowledgments == 1 && sink.lastResponse == Fw::CmdResponse::OK,
          "boot response");
  require(sink.samples == 27, "all channels published");
  for (unsigned i = 0; i < 1800; ++i)
    computer.get_run_InputPort(0)->invoke(0);
  require(sink.values[0] == 1800 && sink.values[18] == 1800,
          "scheduled mission time");
  computer.execute("INJECT_FAULT", 2);
  computer.get_run_InputPort(0)->invoke(0);
  require(sink.values[26] == 2, "sensor autonomous safe");
  computer.execute("PAYLOAD_ON", 0);
  require(sink.lastResponse == Fw::CmdResponse::EXECUTION_ERROR &&
              sink.lastSequence == 3,
          "rejected command terminal response");
  Fw::CmdArgBuffer truncated;
  computer.get_cmdIn_InputPort(0)->invoke(10, 99, truncated);
  require(sink.lastSequence == 99 &&
              sink.lastResponse == Fw::CmdResponse::FORMAT_ERROR,
          "malformed typed argument response");
  std::cout
      << "{\"passed\":true,\"scheduled_ticks\":1801,\"telemetry_samples\":"
      << sink.samples << ",\"terminal_responses\":" << sink.acknowledgments
      << "}\n";
}
