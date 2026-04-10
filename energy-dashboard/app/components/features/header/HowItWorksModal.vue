<template>
  <UModal
    :open="open"
    :ui="{ width: 'max-w-2xl' }"
    @update:open="$emit('update:open', $event)"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <UIcon name="i-heroicons-book-open" class="w-5 h-5 text-blue-400" />
        <div>
          <h3 class="text-base font-semibold text-white">
            How the simulation works
          </h3>
          <p class="text-xs text-gray-400 mt-0.5">
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
            <h4 class="text-white font-semibold">Select your assets</h4>
          </div>
          <p class="text-gray-400 leading-relaxed">
            Use the sidebar to pick <span class="text-amber-400">Supply</span> (generators),
            <span class="text-emerald-400">Demand</span> (loads), and
            <span class="text-blue-400">Network</span> (lines/transformers) components.
            You need at least one supply and one demand to run a simulation.
          </p>
          <div class="mt-2 grid grid-cols-3 gap-2">
            <div class="bg-[#0B1220] rounded p-2 border border-[#1E293B]">
              <p class="text-amber-400 text-xs font-semibold mb-1">Supply (MW)</p>
              <p class="text-gray-500 text-xs">Max power a generator can inject. Wind/solar are weather-limited.</p>
            </div>
            <div class="bg-[#0B1220] rounded p-2 border border-[#1E293B]">
              <p class="text-emerald-400 text-xs font-semibold mb-1">Demand (MW)</p>
              <p class="text-gray-500 text-xs">Peak consumption. Scaled hourly by a normalised load profile.</p>
            </div>
            <div class="bg-[#0B1220] rounded p-2 border border-[#1E293B]">
              <p class="text-blue-400 text-xs font-semibold mb-1">Network (MVA)</p>
              <p class="text-gray-500 text-xs">Lines and transformers with a rated capacity. Overloading is flagged.</p>
            </div>
          </div>
        </section>

        <div class="border-t border-[#1E293B]" />

        <!-- Step 2: Duration -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">2</span>
            <h4 class="text-white font-semibold">Choose a time window</h4>
          </div>
          <p class="text-gray-400 leading-relaxed">
            The simulation runs one AC power flow calculation per hour. Choosing a longer window gives more representative results:
          </p>
          <div class="mt-2 space-y-1.5">
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-mono text-xs w-14 shrink-0 pt-0.5">1 h</span>
              <p class="text-gray-500 text-xs">Single snapshot — good for testing a specific peak moment.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-mono text-xs w-14 shrink-0 pt-0.5">24 h</span>
              <p class="text-gray-500 text-xs">One full day — captures the day/night solar cycle and demand variations.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-mono text-xs w-14 shrink-0 pt-0.5">168 h</span>
              <p class="text-gray-500 text-xs">One week — reveals weekday/weekend load patterns and multi-day wind lulls.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-mono text-xs w-14 shrink-0 pt-0.5">8760 h</span>
              <p class="text-gray-500 text-xs">Full year — most realistic, averages over all seasons and weather events.</p>
            </div>
          </div>
          <div class="mt-2 bg-[#0B1220] rounded p-2 border border-[#1E293B]">
            <p class="text-xs text-gray-400">
              <span class="text-white font-semibold">MW vs MWh:</span>
              MW is instantaneous power (like speed). MWh is energy over time (like distance).
              <span class="text-blue-300">Energy (MWh) = Power (MW) × Hours × Capacity Factor</span>.
              A 500 MW wind farm running at 30% capacity factor for 24 h produces 500 × 24 × 0.30 = <span class="text-emerald-400">3 600 MWh</span>.
            </p>
          </div>
        </section>

        <div class="border-t border-[#1E293B]" />

        <!-- Step 3: Weather data -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">3</span>
            <h4 class="text-white font-semibold">Weather data (wind &amp; solar only)</h4>
          </div>
          <p class="text-gray-400 leading-relaxed">
            When you select a <span class="text-white">date range</span>, the platform fetches real hourly wind speed and solar irradiance data
            from <span class="text-white">KNMI station 06280 — Groningen Eelde</span> (Jan–Dec 2025).
            PyPSA converts this into a capacity factor between 0 and 1 for each hour.
          </p>
          <p class="text-gray-400 leading-relaxed mt-1">
            Without a date range, wind and solar assets run at their full installed capacity — which is unrealistically optimistic.
            Always pick a date range for realistic results.
          </p>
        </section>

        <div class="border-t border-[#1E293B]" />

        <!-- Step 4: PyPSA & AC power flow -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">4</span>
            <h4 class="text-white font-semibold">The AC power flow (PyPSA)</h4>
          </div>
          <p class="text-gray-400 leading-relaxed">
            The backend uses <span class="text-white">PyPSA</span> (Python for Power System Analysis) to run an
            <span class="text-white">AC power flow</span> using the Newton-Raphson method.
            For each hour, it solves the non-linear equations relating voltages, angles, and power injections
            across all buses in the network.
          </p>
          <p class="text-gray-400 leading-relaxed mt-1">
            A simulation <span class="text-emerald-400">converges</span> when the solver finds a physically consistent solution
            (voltages and angles balance). It <span class="text-red-400">does not converge</span> if the network is physically
            infeasible — for example if demand far exceeds available supply, or network parameters are inconsistent.
          </p>
        </section>

        <div class="border-t border-[#1E293B]" />

        <!-- Step 5: Results -->
        <section>
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold shrink-0">5</span>
            <h4 class="text-white font-semibold">Reading the results</h4>
          </div>
          <div class="space-y-1.5">
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Supply (MWh)</span>
              <p class="text-gray-500 text-xs">Total energy injected by all generators over the simulation period.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Demand (MWh)</span>
              <p class="text-gray-500 text-xs">Total energy consumed by all loads over the simulation period.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Balance (MWh)</span>
              <p class="text-gray-500 text-xs">Supply minus Demand. Positive = surplus (grid export). Negative = deficit (grid import).</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Capacity factor</span>
              <p class="text-gray-500 text-xs">Actual energy produced ÷ theoretical maximum. A wind farm at 30% CF produced 30% of what it could at full power 24/7.</p>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-blue-400 font-semibold text-xs w-28 shrink-0 pt-0.5">Line loading %</span>
              <p class="text-gray-500 text-xs">Power flowing through a line as a percentage of its rated MVA capacity. Above 100% = overloaded — reduce connected generation or increase the line rating.</p>
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
