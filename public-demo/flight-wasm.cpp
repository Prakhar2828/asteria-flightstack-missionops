#include "../flight/flight.hpp"
#include <emscripten/emscripten.h>
#include <memory>
namespace {
std::unique_ptr<asteria::Flight> spacecraft;
std::string response;
}
extern "C" {
EMSCRIPTEN_KEEPALIVE void reset_flight(unsigned seed) {
  spacecraft = std::make_unique<asteria::Flight>(seed);
}
EMSCRIPTEN_KEEPALIVE const char* exchange_flight(const char* command, double value) {
  if (!spacecraft) reset_flight(42);
  response = spacecraft->json(spacecraft->apply(command, value));
  return response.c_str();
}
}
