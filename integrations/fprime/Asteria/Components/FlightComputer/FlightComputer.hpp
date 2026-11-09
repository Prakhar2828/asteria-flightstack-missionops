// ======================================================================
// \title  FlightComputer.hpp
// \author prakharpandey
// \brief  hpp file for FlightComputer component implementation class
// ======================================================================

#ifndef Asteria_FlightComputer_HPP
#define Asteria_FlightComputer_HPP

#include "Asteria/Components/FlightComputer/FlightComputerComponentAc.hpp"
#include "flight.hpp"
#include <mutex>

namespace Asteria {

class FlightComputer final : public FlightComputerComponentBase {

public:
  // ----------------------------------------------------------------------
  // Component construction and destruction
  // ----------------------------------------------------------------------

  //! Construct FlightComputer object
  FlightComputer(const char *const compName //!< The component name
  );

  //! Destroy FlightComputer object
  ~FlightComputer();

public:
  void setSeed(U32 seed);
  std::string snapshot();
  std::string frameError(const char *reason);
  void execute(const std::string &command, double value);

private:
  asteria::Flight model;
  asteria::Result lastResult{true, "TELEMETRY"};
  std::mutex modelMutex;
  U32 sequence = 0;
  void applyCommand(const char *command, double value, FwOpcodeType opcode,
                    U32 sequence);
  void publish();
  // ----------------------------------------------------------------------
  // Handler implementations for typed input ports
  // ----------------------------------------------------------------------

  //! Handler implementation for run
  void run_handler(FwIndexType portNum, //!< The port number
                   U32 context          //!< The call order
                   ) override;

private:
  // ----------------------------------------------------------------------
  // Handler implementations for commands
  // ----------------------------------------------------------------------

  //! Handler implementation for command BOOT
  void BOOT_cmdHandler(FwOpcodeType opCode, //!< The opcode
                       U32 cmdSeq           //!< The command sequence number
                       ) override;

  //! Handler implementation for command SAFE
  void SAFE_cmdHandler(FwOpcodeType opCode, //!< The opcode
                       U32 cmdSeq           //!< The command sequence number
                       ) override;

  //! Handler implementation for command RECOVER
  void RECOVER_cmdHandler(FwOpcodeType opCode, //!< The opcode
                          U32 cmdSeq           //!< The command sequence number
                          ) override;

  //! Handler implementation for command RESUME
  void RESUME_cmdHandler(FwOpcodeType opCode, //!< The opcode
                         U32 cmdSeq           //!< The command sequence number
                         ) override;

  //! Handler implementation for command PAYLOAD_ON
  void PAYLOAD_ON_cmdHandler(FwOpcodeType opCode, //!< The opcode
                             U32 cmdSeq //!< The command sequence number
                             ) override;

  //! Handler implementation for command PAYLOAD_OFF
  void PAYLOAD_OFF_cmdHandler(FwOpcodeType opCode, //!< The opcode
                              U32 cmdSeq //!< The command sequence number
                              ) override;

  //! Handler implementation for command HEATER_ON
  void HEATER_ON_cmdHandler(FwOpcodeType opCode, //!< The opcode
                            U32 cmdSeq //!< The command sequence number
                            ) override;

  //! Handler implementation for command HEATER_OFF
  void HEATER_OFF_cmdHandler(FwOpcodeType opCode, //!< The opcode
                             U32 cmdSeq //!< The command sequence number
                             ) override;

  //! Handler implementation for command ADCS_ON
  void ADCS_ON_cmdHandler(FwOpcodeType opCode, //!< The opcode
                          U32 cmdSeq           //!< The command sequence number
                          ) override;

  //! Handler implementation for command ADCS_OFF
  void ADCS_OFF_cmdHandler(FwOpcodeType opCode, //!< The opcode
                           U32 cmdSeq           //!< The command sequence number
                           ) override;

  //! Handler implementation for command POINT
  void POINT_cmdHandler(FwOpcodeType opCode, //!< The opcode
                        U32 cmdSeq,          //!< The command sequence number
                        F64 value) override;

  //! Handler implementation for command DESATURATE
  void DESATURATE_cmdHandler(FwOpcodeType opCode, //!< The opcode
                             U32 cmdSeq //!< The command sequence number
                             ) override;

  //! Handler implementation for command INJECT_FAULT
  void INJECT_FAULT_cmdHandler(FwOpcodeType opCode, //!< The opcode
                               U32 cmdSeq, //!< The command sequence number
                               F64 value) override;

  //! Handler implementation for command CLEAR_FAULTS
  void CLEAR_FAULTS_cmdHandler(FwOpcodeType opCode, //!< The opcode
                               U32 cmdSeq //!< The command sequence number
                               ) override;

  //! Handler implementation for command STEP
  void STEP_cmdHandler(FwOpcodeType opCode, //!< The opcode
                       U32 cmdSeq,          //!< The command sequence number
                       F64 value) override;

  //! Handler implementation for command SNAPSHOT
  void SNAPSHOT_cmdHandler(FwOpcodeType opCode, //!< The opcode
                           U32 cmdSeq           //!< The command sequence number
                           ) override;
};

} // namespace Asteria

#endif
