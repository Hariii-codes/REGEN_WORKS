"""
Carbon Emission Calculator for Waste Items
Calculates CO2 equivalent emissions based on material type and weight
"""

# Carbon emission factors (kg CO2e per kg of material)
# Sources: EPA, IPCC, and industry standards
CARBON_EMISSION_FACTORS = {
    'Plastic': {
        'production': 2.5,  # kg CO2e per kg of plastic produced
        'landfill': 0.05,   # kg CO2e per kg if sent to landfill
        'incineration': 2.8, # kg CO2e per kg if incinerated
        'recycling': -0.5   # Negative = carbon saved by recycling
    },
    'Paper': {
        'production': 1.2,
        'landfill': 0.8,    # Paper in landfill produces methane
        'incineration': 1.5,
        'recycling': -0.3
    },
    'Metal': {
        'production': 3.5,
        'landfill': 0.02,
        'incineration': 0.1,
        'recycling': -2.0   # Metal recycling saves significant energy
    },
    'Glass': {
        'production': 0.9,
        'landfill': 0.01,
        'incineration': 0.05,
        'recycling': -0.2
    },
    'Electronic': {
        'production': 15.0,  # High due to manufacturing complexity
        'landfill': 0.1,
        'incineration': 0.5,
        'recycling': -5.0    # E-waste recycling saves significant resources
    },
    'Organic': {
        'production': 0.5,
        'landfill': 2.0,     # Organic waste in landfill produces methane
        'incineration': 0.3,
        'recycling': -0.1    # Composting
    },
    'Textile': {
        'production': 8.0,
        'landfill': 0.05,
        'incineration': 1.2,
        'recycling': -1.0
    },
    'Unknown': {
        'production': 2.0,
        'landfill': 0.5,
        'incineration': 1.5,
        'recycling': -0.3
    }
}

def calculate_carbon_emissions(material_type, weight_grams, disposal_method='landfill'):
    """
    Calculate carbon emissions for a waste item
    
    Args:
        material_type: Type of material (Plastic, Paper, Metal, etc.)
        weight_grams: Weight in grams
        disposal_method: 'landfill', 'incineration', 'recycling', or 'production'
    
    Returns:
        Dictionary with emission calculations
    """
    # Get emission factors for material
    material = material_type if material_type in CARBON_EMISSION_FACTORS else 'Unknown'
    factors = CARBON_EMISSION_FACTORS.get(material, CARBON_EMISSION_FACTORS['Unknown'])
    
    # Convert grams to kg
    weight_kg = weight_grams / 1000.0
    
    # Calculate emissions based on disposal method
    if disposal_method == 'recycling':
        # Negative value means carbon saved
        co2_emissions = factors['recycling'] * weight_kg
        is_savings = True
    elif disposal_method == 'incineration':
        co2_emissions = factors['incineration'] * weight_kg
        is_savings = False
    elif disposal_method == 'production':
        co2_emissions = factors['production'] * weight_kg
        is_savings = False
    else:  # landfill (default)
        co2_emissions = factors['landfill'] * weight_kg
        is_savings = False
    
    # Calculate equivalent comparisons
    # 1 kg CO2 ≈ driving 2.5 miles in average car
    # 1 kg CO2 ≈ 0.1 tree days of CO2 absorption
    car_miles_equivalent = abs(co2_emissions) * 2.5
    tree_days_equivalent = abs(co2_emissions) * 0.1
    
    return {
        'material_type': material_type,
        'weight_grams': weight_grams,
        'weight_kg': weight_kg,
        'disposal_method': disposal_method,
        'co2_emissions_kg': round(co2_emissions, 4),
        'co2_emissions_grams': round(co2_emissions * 1000, 2),
        'is_carbon_savings': is_savings,
        'car_miles_equivalent': round(car_miles_equivalent, 2),
        'tree_days_equivalent': round(tree_days_equivalent, 2),
        'production_emissions': round(factors['production'] * weight_kg, 4),
        'recycling_savings': round(abs(factors['recycling']) * weight_kg, 4) if factors['recycling'] < 0 else 0
    }

def get_carbon_summary(carbon_data, language='en'):
    """
    Generate a human-readable summary of carbon emissions
    
    Args:
        carbon_data: Dictionary from calculate_carbon_emissions()
        language: Language code for i18n (default: 'en')
    
    Returns:
        Formatted HTML string with carbon emission summary
    """
    from localization_helper import get_localized_string
    
    emissions = carbon_data['co2_emissions_kg']
    is_savings = carbon_data['is_carbon_savings']
    
    if is_savings:
        summary = f"""
        <div class="alert alert-success">
            <h6><i class="fas fa-leaf me-2"></i>{get_localized_string('carbon.savings_title', language, 'Carbon Savings from Recycling')}</h6>
            <p class="mb-1"><strong>{get_localized_string('carbon.co2_saved', language, 'CO2 Saved:')}</strong> {abs(emissions):.4f} kg CO2e</p>
            <p class="mb-1"><strong>{get_localized_string('carbon.equivalent_to', language, 'Equivalent to:')}</strong> {get_localized_string('carbon.driving_fewer_miles', language, 'Driving {miles} fewer miles').format(miles=f"{carbon_data['car_miles_equivalent']:.2f}")}</p>
            <p class="mb-0"><strong>{get_localized_string('carbon.or', language, 'Or:')}</strong> {carbon_data['tree_days_equivalent']:.1f} {get_localized_string('carbon.tree_days', language, 'tree-days of CO2 absorption')}</p>
        </div>
        """
    else:
        summary = f"""
        <div class="alert alert-warning">
            <h6><i class="fas fa-smog me-2"></i>{get_localized_string('carbon.emissions_title', language, 'Carbon Emissions')}</h6>
            <p class="mb-1"><strong>{get_localized_string('carbon.co2_emissions', language, 'CO2 Emissions:')}</strong> {emissions:.4f} kg CO2e</p>
            <p class="mb-1"><strong>{get_localized_string('carbon.equivalent_to', language, 'Equivalent to:')}</strong> {get_localized_string('carbon.driving_miles', language, 'Driving {miles} miles in a car').format(miles=f"{carbon_data['car_miles_equivalent']:.2f}")}</p>
            <p class="mb-1"><strong>{get_localized_string('carbon.or', language, 'Or:')}</strong> {carbon_data['tree_days_equivalent']:.1f} {get_localized_string('carbon.tree_days_needed', language, 'tree-days of CO2 absorption needed')}</p>
            <p class="mb-0"><small class="text-muted">
                <strong>{get_localized_string('carbon.tip', language, 'Tip:')}</strong> {get_localized_string('carbon.recycling_tip', language, 'Recycling this item could save {savings} kg CO2e!').format(savings=f"{carbon_data['recycling_savings']:.4f}")}
            </small></p>
        </div>
        """
    
    return summary

