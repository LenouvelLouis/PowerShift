Feature: US-05 — Nuclear supply for residential network
  As a researcher,
  I want to simulate a network where one nuclear power plant supplies multiple houses over a fixed time period,
  so that I can validate energy distribution across a residential network.

  Background:
    Given a nuclear power plant producing 100 kWh
    And 10 houses each consuming 10 kWh
    And the simulation runs for 1 hour

  Scenario: Total supply matches total consumption
    When I run the simulation
    Then total supply is 100.0 kWh
    And total demand is 100.0 kWh
    And the energy balance is 0.0 kWh

  Scenario: All houses receive equal energy
    When I run the simulation
    Then every house receives the same amount of energy
    And each house receives 10.0 kWh

  Scenario: Network remains stable during the simulation
    When I run the simulation
    Then the simulation status is "optimal"
    And the network shows no overload

  Scenario: UI displays per-house consumption
    When I run the simulation
    Then the result includes consumption data for all 10 houses