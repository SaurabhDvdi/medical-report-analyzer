import math

def calculate_velocity(flow_rate, diameter):
    area = math.pi * (diameter/2)**2
    return flow_rate / area

def calculate_risk(blockage_percent):
    if blockage_percent < 30:
        return "Low"
    elif blockage_percent < 70:
        return "Medium"
    else:
        return "High"

def simulate(blockage_percent):
    base_diameter = 4  # mm
    reduced_diameter = base_diameter * (1 - blockage_percent/100)

    velocity = calculate_velocity(flow_rate=5, diameter=reduced_diameter)
    risk = calculate_risk(blockage_percent)

    return {
        "diameter": reduced_diameter,
        "velocity": velocity,
        "risk": risk
    }