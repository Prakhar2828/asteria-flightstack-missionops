register_fprime_executable(AsteriaBridge SOURCES "${CMAKE_CURRENT_LIST_DIR}/main.cpp" DEPENDS Asteria_Components_FlightComputer)
register_fprime_executable(AsteriaVerification SOURCES "${CMAKE_CURRENT_LIST_DIR}/verification.cpp" DEPENDS Asteria_Components_FlightComputer)
