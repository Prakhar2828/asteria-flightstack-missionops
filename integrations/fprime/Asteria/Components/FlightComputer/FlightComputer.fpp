module Asteria {
  passive component FlightComputer {
    sync input port run: Svc.Sched
    time get port timeCaller
    import Fw.Command
    import Fw.Event
    import Fw.Channel
    sync command BOOT opcode 0
    sync command SAFE opcode 1
    sync command RECOVER opcode 2
    sync command RESUME opcode 3
    sync command PAYLOAD_ON opcode 4
    sync command PAYLOAD_OFF opcode 5
    sync command HEATER_ON opcode 6
    sync command HEATER_OFF opcode 7
    sync command ADCS_ON opcode 8
    sync command ADCS_OFF opcode 9
    sync command POINT(value: F64) opcode 10
    sync command DESATURATE opcode 11
    sync command INJECT_FAULT(value: F64) opcode 12
    sync command CLEAR_FAULTS opcode 13
    sync command STEP(value: F64) opcode 14
    sync command SNAPSHOT opcode 15
    telemetry Time: F64 id 0
    telemetry BatterySoc: F64 id 1
    telemetry BusVoltage: F64 id 2
    telemetry SolarPower: F64 id 3
    telemetry LoadPower: F64 id 4
    telemetry Temperature: F64 id 5
    telemetry Heater: F64 id 6
    telemetry Attitude: F64 id 7
    telemetry AngularRate: F64 id 8
    telemetry WheelRpm: F64 id 9
    telemetry TargetAngle: F64 id 10
    telemetry SensorAge: F64 id 11
    telemetry AdcsEnabled: F64 id 12
    telemetry LinkConnected: F64 id 13
    telemetry LinkAge: F64 id 14
    telemetry Packets: F64 id 15
    telemetry PayloadEnabled: F64 id 16
    telemetry PayloadData: F64 id 17
    telemetry Ticks: F64 id 18
    telemetry MissedDeadlines: F64 id 19
    telemetry CommandsAccepted: F64 id 20
    telemetry CommandsRejected: F64 id 21
    telemetry OrbitPhase: F64 id 22
    telemetry Sunlight: F64 id 23
    telemetry Healthy: F64 id 24
    telemetry HealthyDwell: F64 id 25
    telemetry Mode: U32 id 26
    event ModeChanged(mode: U32) severity activity high id 0 format "Mode {}"
    event CommandRejected(commandId: U32) severity warning high id 1 format "Rejected command {}"
  }
}
