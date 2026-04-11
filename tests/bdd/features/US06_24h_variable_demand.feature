Feature: US-06 — Time variation over 24 hours with variable demand
  As a researcher,
  I want to simulate energy distribution over 24 hours with variable demand,
  so that I can analyze realistic consumption behavior across a residential network.

  Background:
    Given a nuclear generator with 100 MW capacity
    And 10 houses with variable 24h demand profiles
    And no network component

  Scenario: Simulation completes over 24 time steps
    When I run a 24-hour simulation
    Then the simulation status is "optimal"
    And the simulation covers exactly 24 time steps

  Scenario: Power balance is maintained at every hour
    When I run a 24-hour simulation
    Then the energy balance is close to 0.0 MWh over 24 hours

  Scenario: Demand varies across the 24 hours
    When I run a 24-hour simulation
    Then the total demand is not constant across all hours

  Scenario: Nuclear plant never exceeds its capacity
    When I run a 24-hour simulation
    Then the nuclear plant output never exceeds 100 MW

  Scenario: Evening peak is higher than night valley
    When I run a 24-hour simulation
    Then the demand at hours 18 to 20 is higher than at hours 1 to 3

  Scenario: All 10 houses are present in the simulation
    When I run a 24-hour simulation
    Then the network contains exactly 10 house loads
