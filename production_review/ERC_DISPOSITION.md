# ERC disposition

KiCad 10.0.6 reported **0 ERC violations** on the current R10 schematic hierarchy under the configured project profile.

The configured profile ignores: single_global_label, four_way_junction, simulation_model_issue, footprint_filter. A strict audit copy enabled those categories as warnings and reported **0 violations with 0 ignored checks**. This is a native strict-profile ERC pass.

The strict rule changes were applied only to an isolated Git worktree. No active schematic or project file was modified or converted by either run.
