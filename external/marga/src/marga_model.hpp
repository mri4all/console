#ifndef MARGA_MODEL_HPP
#define MARGA_MODEL_HPP

#include "verilated.h"
class Vmarga_model;
struct marga_csv;
static const unsigned CSV_VERSION_MAJOR = 0, CSV_VERSION_MINOR = 2;

class marga_model {
public:
	vluint64_t MAX_SIM_TIME;
	Vmarga_model *vmm;
	VerilatedFstC *tfp;
	marga_csv *csv;
	bool _fst_output = false, _csv_output = false;

	marga_model(int argc, char *argv[]);
	~marga_model();

	// If system's finished, return -1; otherwise 0
	int tick();

	// Reads and writes must be relative to marga's memory space
	// (i.e. slave reg 0 has address 0x0, slave reg 1 has address
	// 0x4, etc
	uint32_t rd32(uint32_t mar_addr);
	void wr32(uint32_t mar_addr, uint32_t data);
};

#endif
