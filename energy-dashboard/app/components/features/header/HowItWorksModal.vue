<template>
  <UModal
    :open="open"
    class="max-w-2xl"
    @update:open="$emit('update:open', $event)"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <UIcon
          name="i-heroicons-book-open"
          class="w-5 h-5 text-blue-400"
        />
        <div>
          <h3 class="text-base font-semibold text-gray-900 dark:text-white">
            How the simulation works
          </h3>
          <p class="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
            A step-by-step guide to understanding the platform
          </p>
        </div>
      </div>
    </template>

    <template #body>
      <div class="space-y-6 max-h-[70vh] overflow-y-auto pr-1 text-sm">
        <!-- Step 1: Asset selection -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">1</span>
            <h4 class="text-gray-900 dark:text-white font-semibold">
              Select your assets
            </h4>
          </div>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">
            Use the sidebar to pick <span class="text-amber-400">Supply</span> (generators),
            <span class="text-emerald-400">Demand</span> (loads), and
            <span class="text-blue-400">Network</span> (lines/transformers) components.
            You need at least one supply and one demand to run a simulation.
          </p>
          <div class="mt-2 grid grid-cols-3 gap-2">
            <div class="bg-gray-50 dark:bg-slate-950 rounded p-2 border border-gray-200 dark:border-slate-800">
              <p class="text-amber-400 text-xs font-semibold mb-1">
                Supply (MW)
              </p>
              <p class="text-gray-500 text-xs">
                Max power a generator can inject. Wind/solar are weather-limited.
              </p>
            </div>
            <div class="bg-gray-50 dark:bg-slate-950 rounded p-2 border border-gray-200 dark:border-slate-800">
              <p class="text-emerald-400 text-xs font-semibold mb-1">
                Demand (MW)
              </p>
              <p class="text-gray-500 text-xs">
                Peak consumption. Scaled hourly by a normalised load profile.
              </p>
            </div>
            <div class="bg-gray-50 dark:bg-slate-950 rounded p-2 border border-gray-200 dark:border-slate-800">
              <p class="text-blue-400 text-xs font-semibold mb-1">
                Network (MVA)
              </p>
              <p class="text-gray-500 text-xs">
                Lines and transformers with a rated capacity. Overloading is flagged.
              </p>
            </div>
          </div>
        </section>

        <div class="border-t border-gray-200 dark:border-slate-800" />

        <!-- Step 2: Duration -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">2</span>
            <h4 class="text-gray-900 dark:text-white font-semibold">
              Choose a time window
            </h4>
          </div>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">
            The optimizer solves all hours simultaneously. Choosing a longer window gives more representative results:
          </p>
          <div class="mt-2 space-y-1.5">
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-mono text-xs w-14 shrink-0 pt-0.5">1 h</span>
              <p class="text-gray-500 text-xs">
                Single snapshot — good for testing a specific peak moment.
              </p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-mono text-xs w-14 shrink-0 pt-0.5">24 h</span>
              <p class="text-gray-500 text-xs">
                One full day — captures the day/night solar cycle and demand variations.
              </p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-mono text-xs w-14 shrink-0 pt-0.5">168 h</span>
              <p class="text-gray-500 text-xs">
                One week — reveals weekday/weekend load patterns and multi-day wind lulls.
              </p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-mono text-xs w-14 shrink-0 pt-0.5">8760 h</span>
              <p class="text-gray-500 text-xs">
                Full year — most realistic, averages over all seasons and weather events.
              </p>
            </div>
          </div>
          <div class="mt-2 bg-gray-50 dark:bg-slate-950 rounded p-2 border border-gray-200 dark:border-slate-800">
            <p class="text-xs text-gray-600 dark:text-gray-400">
              <span class="text-gray-900 dark:text-white font-semibold">MW vs MWh:</span>
              MW is instantaneous power (like speed). MWh is energy over time (like distance).
              <span class="text-blue-300">Energy (MWh) = Power (MW) × Hours × Capacity Factor</span>.
              A 500 MW wind farm running at 30% capacity factor for 24 h produces 500 × 24 × 0.30 = <span class="text-emerald-400">3 600 MWh</span>.
            </p>
          </div>
        </section>

        <div class="border-t border-gray-200 dark:border-slate-800" />

        <!-- Step 3: Weather data -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">3</span>
            <h4 class="text-gray-900 dark:text-white font-semibold">
              Weather data (wind &amp; solar only)
            </h4>
          </div>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">
            When you select a <span class="text-gray-900 dark:text-white">date range</span>, the platform fetches real hourly wind speed and solar irradiance data
            from <span class="text-gray-900 dark:text-white">KNMI station 06280 — Groningen Eelde</span> (Jan–Dec 2025).
            PyPSA converts this into a capacity factor between 0 and 1 for each hour.
          </p>
          <p class="text-gray-400 leading-relaxed mt-1">
            Without a date range, wind and solar assets run at their full installed capacity — which is unrealistically optimistic.
            Always pick a date range for realistic results.
          </p>
        </section>

        <div class="border-t border-gray-200 dark:border-slate-800" />

        <!-- Step 4: PyPSA & LOPF -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">4</span>
            <h4 class="text-gray-900 dark:text-white font-semibold">
              The optimizer (PyPSA LOPF)
            </h4>
          </div>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">
            The backend uses <span class="text-gray-900 dark:text-white">PyPSA</span> (Python for Power System Analysis) with
            <span class="text-gray-900 dark:text-white">Linear Optimal Power Flow (LOPF)</span> solved by HiGHS.
            Instead of fixing the dispatch manually, the optimizer finds the cheapest dispatch schedule
            across all hours simultaneously — prioritizing free renewables, then cheaper conventional generators,
            and reserving the grid connection as a last resort.
          </p>
          <p class="text-gray-400 leading-relaxed mt-1">
            Battery storage (if selected) is handled as a <span class="text-gray-900 dark:text-white">StorageUnit</span>:
            the optimizer charges it during surplus hours and discharges it when generation is short,
            minimizing curtailment and grid imports. A simulation is <span class="text-emerald-400">optimised</span>
            when HiGHS finds an optimal solution, or returns an error if the problem is infeasible.
          </p>
        </section>

        <div class="border-t border-gray-200 dark:border-slate-800" />

        <!-- Step 5: Results -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">5</span>
            <h4 class="text-gray-900 dark:text-white font-semibold">
              Reading the results
            </h4>
          </div>
          <div class="space-y-1.5">
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Supply (MWh)</span>
              <p class="text-gray-500 text-xs">
                Total energy injected by all generators over the simulation period.
              </p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Demand (MWh)</span>
              <p class="text-gray-500 text-xs">
                Total energy consumed by all loads over the simulation period.
              </p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Balance (MWh)</span>
              <p class="text-gray-500 text-xs">
                Supply minus Demand. Positive = surplus (grid export). Negative = deficit (grid import).
              </p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Capacity factor</span>
              <p class="text-gray-500 text-xs">
                Actual energy produced ÷ theoretical maximum. A wind farm at 30% CF produced 30% of what it could at full power 24/7.
              </p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Line loading %</span>
              <p class="text-gray-500 text-xs">
                Power flowing through a line as a percentage of its rated MVA capacity. Above 100% = overloaded — reduce connected generation or increase the line rating.
              </p>
            </div>
          </div>
        </section>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-end">
        <UButton
          label="Close"
          color="neutral"
          variant="ghost"
          @click="$emit('update:open', false)"
        />
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
defineProps<{ open: boolean }>()
defineEmits<{ 'update:open': [value: boolean] }>()
</script>
