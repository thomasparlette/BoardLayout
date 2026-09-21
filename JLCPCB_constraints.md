# JLCPCB fabrication review - 14 September 2026

Manufacturer changed to JLCPCB at the user's request. Reference: https://jlcpcb.com/capabilities/pcb-capabilities

The published multilayer 2 oz track/space minimum is 0.15/0.15 mm. R6 default low-current signal routing uses 0.20/0.20 mm, with some existing 0.25 mm traces retained. Wider load and rail classes retain their targets. JLCPCB lists a 0.254 mm or greater PTH annular ring for 2 oz. The Q1/Q2 draft footprints have only 0.15 mm rings and therefore need revision before a 2 oz release. Increasing the pad diameter alone conflicts with their present pitch.

The page distinguishes via and component-hole rules. Existing vias are 0.8 mm diameter with 0.4 mm drills. The inner copper default is 0.5 oz; do not assume that selecting 2 oz outer copper makes the inner layers 2 oz. Explicit stackup selection and confirmation remain required.

The routing calculations currently assume 70 um copper. This is a proposed build assumption, not a released JLCPCB stackup. Do not order using defaults. Hole plating, copper tolerances, soldermask, legend and the final outline also need fabrication checks.

Factory mounting geometry is retained. JLCPCB manufacturability does not establish the electrical spacing needed around ignition switching nodes, temperature rise, automotive transient immunity, or component compatibility. Those remain separate engineering requirements.
