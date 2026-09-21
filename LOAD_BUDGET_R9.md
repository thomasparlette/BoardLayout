# R9 routing load basis — provisional

- Four wasted-spark primary channels. User target: 6 A peak operating current, to be measured on the bench. Earlier 4 A RMS applies per coil pack, not each primary. Keep 10 A transient routing allowance per primary until characterized. This PCB does not establish or enforce a 6 A current limit by itself.
- Bosch OE 62395 high-impedance injectors, 11–18 ohms. Published MS3X 5 A channel specification is a reference rating, not proof that the replacement copper or selected devices meet it.
- Factory F6AZ-9F715-EB IAC: 1.0–1.2 A, user-specified 300 Hz PWM.
- External MicroSquirt V3 controls 4R70W. SSA/SSB 0.4–0.6 A; TCC 0.7–1.2 A. EPC 2.1–4.8 A supplied as a resistance-derived range, not a verified RMS waveform. Pass-through contacts and shared return paths require combined-load qualification.
- Remaining unspecified outputs: 1.5 A maximum each. Fuel pump, fan and A/C outputs drive relay coils only.
- ECU input uses factory 30 A upstream fuse. This is not a rating for each PCB trace or a substitute for coordinated board protection.
- Wideband controllers have external power; old heater outputs switch relay/enable loads. MapDaddy supplies MAP and barometric signals.

Trace widths and via arrays are provisional. Final copper weights, temperature rise, duty cycles, driver losses, connector ratings and case thermal interfaces require review before manufacture. The six-layer option preserves the mechanical test-board dimensions and component placements; actual manufacturer stackup is not selected.
