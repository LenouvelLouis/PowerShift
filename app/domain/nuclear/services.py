# app/domain/nuclear/services.py

from __future__ import annotations

from app.domain.nuclear.entities import NuclearReactor


class NuclearConstraintsBuilder:
    @staticmethod
    def build_pypsa_params(reactor: NuclearReactor) -> dict:
        """
        Returns kwargs for n.add('Generator', ...)

        Notes:
        - No p_max_pu on purpose.
        - Nuclear can dispatch freely up to p_nom.
        - We expose unit-commitment related constraints if PyPSA is configured to use them.
        """
        return {
            "committable": True,
            "p_min_pu": reactor.p_min_pu,
            "ramp_limit_up": reactor.ramp_rate_pu_per_hour,
            "ramp_limit_down": reactor.ramp_rate_pu_per_hour,
            "min_up_time": reactor.min_up_time_h,
            "min_down_time": reactor.min_down_time_h,
            "start_up_cost": reactor.startup_cost,
            "marginal_cost": reactor.marginal_cost_per_mwh,
        }