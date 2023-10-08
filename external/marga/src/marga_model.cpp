#include "marga_model.hpp"
#include "version.hpp"

#include "Vmarga_model.h"
#include "verilated_fst_c.h"

#include <iostream>
#include <string>

using namespace std;

vluint64_t main_time = 0;

struct marga_csv {
	// TX
	uint16_t tx0_i = 0, tx0_q = 0, tx1_i = 0, tx1_q = 0;
	uint16_t fhdo_voutx = 0, fhdo_vouty = 0, fhdo_voutz = 0, fhdo_voutz2 = 0;
	uint32_t ocra1_voutx = 0, ocra1_vouty = 0, ocra1_voutz = 0, ocra1_voutz2 = 0xfffff; // last is different purely so that a difference is picked up on the first row's write
	uint16_t rx0_rate = 0, rx1_rate = 0;
	uint8_t rx0_rate_valid = 0, rx1_rate_valid = 0, rx0_rst_n_o = 0, rx1_rst_n_o = 0, rx0_en_o = 0, rx1_en_o = 0;
	uint8_t tx_gate = 0, rx_gate = 0, trig = 0, leds = 0;

	FILE *f;
	unsigned _line = 0;
	const unsigned _LINE_INTERVAL = 15; // how many lines between column label insertions
	string _colnames{"#  ticks, tx0_i, tx0_q, tx1_i, tx1_q, fhd_x, fhd_y, fhd_z,fhd_z2,  oc1_x,  oc1_y,  oc1_z, oc1_z2, rx0r, rx1r,v0,v1,r0,r1,e0,e1,tg,rg,to,leds\n"};

	marga_csv(const char *filename) {
		f = fopen(filename, "w");
		if (f == nullptr) {
			char errstr[1024];
			sprintf(errstr, "Could not open %s\n", filename);
			throw runtime_error(errstr);
		}
		wr_header();
	}

	~marga_csv() {
		fclose(f);
	}

	void wr_header() {
		// full header
		fprintf(f, "# clock cycles, tx0_i, tx0_q, tx1_i, tx1_q,"
		        " fhdo_vx, fhdo_vy, fhdo_vz, fhdo_vz2, ocra1_vx, ocra1_vy, ocra1_vz, ocra1_vz2,"
		        " rx0_rate, rx1_rate, rx0_rate_valid, rx1_rate_valid, rx0_rst_n, rx1_rst_n, rx0_en, rx1_en,"
		        " tx_gate, rx_gate, trig_out, leds, csv_version_%d.%d\n", CSV_VERSION_MAJOR, CSV_VERSION_MINOR);
	}

	bool wr_update(Vmarga_model *fm) {
		// Long and ugly - I'm sorry!
		bool diff_tx = false, diff_grad = false, diff_rx = false, diff_gpio = false;

		if (false and main_time/10 == 211845) { // debugging only: breakpoint at particular time
			printf("x\n");
		}

		if (fm->tx0_i != tx0_i) { tx0_i = fm->tx0_i; diff_tx = true; }
		if (fm->tx0_q != tx0_q) { tx0_q = fm->tx0_q; diff_tx = true; }
		if (fm->tx1_i != tx1_i) { tx1_i = fm->tx1_i; diff_tx = true; }
		if (fm->tx1_q != tx1_q) { tx1_q = fm->tx1_q; diff_tx = true; }

		if (fm->fhdo_voutx != fhdo_voutx) { fhdo_voutx = fm->fhdo_voutx; diff_grad = true; }
		if (fm->fhdo_vouty != fhdo_vouty) { fhdo_vouty = fm->fhdo_vouty; diff_grad = true; }
		if (fm->fhdo_voutz != fhdo_voutz) { fhdo_voutz = fm->fhdo_voutz; diff_grad = true; }
		if (fm->fhdo_voutz2 != fhdo_voutz2) { fhdo_voutz2 = fm->fhdo_voutz2; diff_grad = true; }

		if (fm->ocra1_voutx != ocra1_voutx) { ocra1_voutx = fm->ocra1_voutx; diff_grad = true; }
		if (fm->ocra1_vouty != ocra1_vouty) { ocra1_vouty = fm->ocra1_vouty; diff_grad = true; }
		if (fm->ocra1_voutz != ocra1_voutz) { ocra1_voutz = fm->ocra1_voutz; diff_grad = true; }
		if (fm->ocra1_voutz2 != ocra1_voutz2) { ocra1_voutz2 = fm->ocra1_voutz2; diff_grad = true; }

		if (fm->rx0_rate != rx0_rate) { rx0_rate = fm->rx0_rate; diff_rx = true; }
		if (fm->rx1_rate != rx1_rate) { rx1_rate = fm->rx1_rate; diff_rx = true; }
		if (fm->rx0_rate_valid != rx0_rate_valid) { rx0_rate_valid = fm->rx0_rate_valid; diff_rx = true; }
		if (fm->rx1_rate_valid != rx1_rate_valid) { rx1_rate_valid = fm->rx1_rate_valid; diff_rx = true; }
		if (fm->rx0_rst_n_o != rx0_rst_n_o) { rx0_rst_n_o = fm->rx0_rst_n_o; diff_rx = true; }
		if (fm->rx1_rst_n_o != rx1_rst_n_o) { rx1_rst_n_o = fm->rx1_rst_n_o; diff_rx = true; }
		if (fm->rx0_en_o != rx0_en_o) { rx0_en_o = fm->rx0_en_o; diff_rx = true; }
		if (fm->rx1_en_o != rx1_en_o) { rx1_en_o = fm->rx1_en_o; diff_rx = true; }

		if (fm->tx_gate_o != tx_gate) { tx_gate = fm->tx_gate_o; diff_gpio = true; }
		if (fm->rx_gate_o != rx_gate) { rx_gate = fm->rx_gate_o; diff_gpio = true; }
		if (fm->trig_o != trig) { trig = fm->trig_o; diff_gpio = true; }
		if (fm->leds_o != leds) { leds = fm->leds_o; diff_gpio = true; }

		bool diff = diff_tx or diff_grad or diff_rx or diff_gpio;
		if (diff) {
			// occasionally print abridged column names for easy reading
			if (_line++ % _LINE_INTERVAL == 0) {
				fprintf(f, _colnames.c_str());
			}

			fprintf(f, "%8lu, %5d, %5d, %5d, %5d, "
			        "%5u, %5u, %5u, %5u, "
			        "%6d, %6d, %6d, %6d,"
			        "%5u,%5u, %1d, %1d, "
			        "%1d, %1d, %1d, %1d, "
			        "%1d, %1d, %1d, %3u\n",
			        main_time/10, tx0_i, tx0_q, tx1_i, tx1_q,
			        fhdo_voutx, fhdo_vouty, fhdo_voutz, fhdo_voutz2,
			        ocra1_voutx, ocra1_vouty, ocra1_voutz, ocra1_voutz2,
			        rx0_rate, rx1_rate, rx0_rate_valid, rx1_rate_valid,
			        rx0_rst_n_o, rx1_rst_n_o, rx0_en_o, rx1_en_o,
			        tx_gate, rx_gate, trig, leds);
		}
		return diff;
	}
};

marga_model::marga_model(int argc, char *argv[]) : MAX_SIM_TIME(200e6) {
	auto filepath_csv = string(argv[0]) + ".csv", filepath_fst = string(argv[0]) + ".fst";
	if (argc > 1) {
		string csvs("csv"), fsts("fst"), boths("both");

		if (csvs.compare(argv[1]) == 0) {
			if (argc > 2) filepath_csv = argv[2];
			printf("Dumping event output to %s\n", filepath_csv.c_str());
			_csv_output = true;
		} else if (fsts.compare(argv[1]) == 0) {
			if (argc > 2) filepath_fst = argv[2];
			printf("Saving FST trace to %s\n", filepath_fst.c_str());
			_fst_output = true;
		} else if (boths.compare(argv[1]) == 0) {
			if (argc > 2) filepath_csv = argv[2];
			if (argc > 3) filepath_fst = argv[3];

			printf("Saving FST trace to %s\n", filepath_fst.c_str());
			printf("Dumping event output to %s\n", filepath_csv.c_str());
			_fst_output = true;
			_csv_output = true;
		} else {
			printf("Unknown argument; only accepting fst or csv for now. No data will be dumped.\n");
		}
	} else {
		printf("\n\t Usage: %s DUMPTYPE DUMPPATH(S)\n", argv[0]);
		printf("\t where DUMPTYPE (optional) is csv, fst or 'both', DUMPPATH (optional) is (are) non-default output file paths.\n");
		printf("\t Examples:\n");
		printf("\t\t%s # (no dump files will be produced)\n", argv[0]);
		printf("\t\t%s csv # (will dump to %s.csv)\n", argv[0], argv[0]);
		printf("\t\t%s csv /path/to/test.csv\n", argv[0]);
		printf("\t\t%s fst # (will dump to %s.fst)\n", argv[0], argv[0]);
		printf("\t\t%s fst /path/to/test.fst\n", argv[0]);
		printf("\t\t%s both # (will dump to %s.csv and %s.fst)\n", argv[0], argv[0], argv[0]);
		printf("\t\t%s both /path/to/test.csv /path/to/test2.fst\n", argv[0]);
		printf("\n\t Hit ctrl-c to halt the program.\n");
	}

	Verilated::commandArgs(argc, argv);
	vmm = new Vmarga_model;

	if (_fst_output) {
		Verilated::traceEverOn(true);
		tfp = new VerilatedFstC;

		vmm->trace(tfp, 10);
		tfp->open(filepath_fst.c_str());
	}

	if (_csv_output) {
		csv = new marga_csv(filepath_csv.c_str());
	}

	// Init
	vmm->s0_axi_aclk = 1;
	vmm->trig_i = 0;

	// AXI slave bus
	vmm->s0_axi_awaddr = 0;
	vmm->s0_axi_wdata = 0;
	vmm->s0_axi_araddr = 0;

	vmm->s0_axi_aresetn = 0;
	vmm->s0_axi_awprot = 0;
	vmm->s0_axi_awvalid = 0;
	vmm->s0_axi_wstrb = 0;
	vmm->s0_axi_wvalid = 0;
	vmm->s0_axi_bready = 0;
	vmm->s0_axi_arprot = 0;
	vmm->s0_axi_arvalid = 0;
	vmm->s0_axi_rready = 0;

	// Wait 5 cycles
	for (int k = 0; k < 10; ++k) tick();

	// End reset, followed by 5 more cycles
	vmm->s0_axi_aresetn = 1;
	vmm->s0_axi_bready = 1;

	for (int k = 0; k < 10; ++k) tick();
}

marga_model::~marga_model() {
	vmm->final();
	delete vmm;
	if (_fst_output) delete tfp;
	if (_csv_output) delete csv;
}

int marga_model::tick() {
	if (main_time < MAX_SIM_TIME) {
		// TODO: progress bar

		if (_fst_output) tfp->dump(main_time); // NOTE: time in ns assuming 100 MHz clock

		// update clock
		vmm->s0_axi_aclk = !vmm->s0_axi_aclk;

		vmm->eval();

		if (vmm->s0_axi_aclk == 0 and _csv_output) csv->wr_update(vmm); // only update on negative edges of the clock
		main_time += 5; // increment time after CSV was written
		return 0;
	} else {
		return -1;
	}
}

uint32_t marga_model::rd32(uint32_t addr) {
	static const unsigned READ_TICKS_SLOW = 10000;

	tick();

	vmm->s0_axi_arvalid = 1;
	vmm->s0_axi_araddr = addr;

	// wait for address to be accepted
	unsigned read_ticks = 0;
	while (!vmm->s0_axi_arready) {
		tick();
		read_ticks++;
		if (read_ticks > READ_TICKS_SLOW) {
			cout << main_time << "ns: Slow to accept read address " << addr << endl;
			read_ticks = 0;
			break;
		}
	}

	read_ticks = 0;

	while (!vmm->s0_axi_rvalid) {
		tick();
		read_ticks++;
		if (read_ticks > READ_TICKS_SLOW) {
			cout << main_time << "ns: Slow to return data at address " << addr << endl;
			read_ticks = 0;
			break;
		}
	}
	tick();
	uint32_t data = vmm->s0_axi_rdata; // save data from bus

	vmm->s0_axi_arvalid = 0;
	vmm->s0_axi_rready = 1;
	tick(); tick(); // 1 full clock cycle
	vmm->s0_axi_rready = 0;

	return data;
}

void marga_model::wr32(uint32_t addr, uint32_t data) {
	static const unsigned WRITE_TICKS_SLOW = 10000;

	tick();

	vmm->s0_axi_wdata = data;
	vmm->s0_axi_awaddr = addr;
	vmm->s0_axi_awvalid = 1;
	vmm->s0_axi_wvalid = 1;

	// wait for marga to be ready
	unsigned write_ticks = 0;
	while (! (vmm->s0_axi_awready and vmm->s0_axi_wready) ) {
		tick();
		write_ticks++;
		if (write_ticks > WRITE_TICKS_SLOW) {
			cout << main_time << ": Slow to write to address " << addr << endl;
			write_ticks = 0;
			break;
		}
	}

	// end bus transaction
	tick();tick();
	vmm->s0_axi_awvalid = 0;
	vmm->s0_axi_wvalid = 0;

	tick();
}
