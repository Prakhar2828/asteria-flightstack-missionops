#include "flight.hpp"
#include <iostream>
#include <limits>
int main(int argc,char** argv) {
 std::uint32_t seed=42;
 try { if(argc>1) {std::size_t n;auto s=std::stoull(argv[1],&n);if(n!=std::string(argv[1]).size()||s>std::numeric_limits<std::uint32_t>::max())return 2;seed=static_cast<std::uint32_t>(s);} } catch(...) {return 2;}
 asteria::Flight flight(seed);
 char buffer[258];
 while(std::cin.getline(buffer,sizeof(buffer)) || !std::cin.eof()) {
  if(std::cin.fail()){std::cin.clear();std::cin.ignore(std::numeric_limits<std::streamsize>::max(),'\n');std::cout<<flight.json({false,"FRAME_TOO_LARGE"})<<std::endl;continue;}
  const std::string line(buffer,static_cast<std::size_t>(std::cin.gcount()-(std::cin.eof()?0:1)));
  if(line.size()>256){std::cout<<flight.json({false,"FRAME_TOO_LARGE"})<<std::endl;continue;}
  std::istringstream input(line);std::string cmd,extra;double value=0;
  if(!(input>>cmd>>value)||(input>>extra)||cmd.size()>32||cmd.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZ_")!=std::string::npos){std::cout<<flight.json({false,"MALFORMED_FRAME"})<<std::endl;continue;}
  std::cout<<flight.json(flight.apply(cmd,value))<<std::endl;
 }
}
