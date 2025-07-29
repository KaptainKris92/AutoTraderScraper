# Not including model since conditional drop-down would be too much work atm.  
possible_params = ['postcode', 
                   'radius', 
                   'make',                     
                   'min_price', 
                   'max_price',
                   'min_reg_year',
                   'max_reg_year',
                   'min_mileage', 
                   'max_mileage',
                   'gearbox',
                   'body_type',
                   'colour',
                   'doors',
                   'seats',
                   'fuel type',
                   'min_engine_size',
                   'max_engine_size',
                   'min_engine_power',
                   'max_engine_power',
                   'acceleration',
                   'fuel_consumption',
                   'co2_emissions',
                   'tax_per_year',
                   'insurance_group',
                   'drive_type',
                   'boot_space',
                   'seller_type',
                   'previously_written_off'
                   ]

search_mapping = {'postcode': lambda x: f'postcode={x}', 
                   'radius': lambda x: f'radius={x}', 
                   'make': lambda x: f'make={x}',                     
                   'min_price': lambda x: f'price-from={x}', 
                   'max_price': lambda x: f'price-to={x}',
                   'min_reg_year': lambda x: f'year-from={x}',
                   'max_reg_year': lambda x: f'year-to={x}',
                   'min_mileage': lambda x: f'minimum-mileage={x}', 
                   'max_mileage': lambda x: f'maximum-mileage={x}',
                   'gearbox': lambda x: f'transmission={x}',
                   'body_type': lambda x: f'body-type={x}',
                   'colour': lambda x: f'colour={x}',
                   'doors': lambda x: f'quantity-of-doors={x}',
                   'seats': lambda x: f'seats_values={x}',
                   'fuel type': lambda x: f'fuel-type={x}',
                   'min_engine_size': lambda x: f'minimum-badge-engine-size={x}',
                   'max_engine_size': lambda x: f'maximum-badge-engine-size={x}',
                   'min_engine_power': lambda x: f'min-engine-power={x}',
                   'max_engine_power': lambda x: f'max-engine-power={x}',
                   'acceleration': lambda x: f'zero-to-60={x}',
                   'fuel_consumption': lambda x: f'fuel-consumption={x}',
                   'co2_emissions': lambda x: f'co2-emissions-cars={x}',
                   'tax_per_year': lambda x: f'annual-tax-cars={x}',
                   'insurance_group': lambda x: f'insuranceGroup={x}',
                   'drive_type': lambda x: f'drivetrain={x}',
                   'boot_space': lambda x: f'bootSizeValues={x}',
                   'seller_type': lambda x: f'seller-type={x}',
                   'previously_written_off': lambda x: f'exclude-writeoff-categories={x}'
                   }

def generate_autotrader_url(params):
    base = "https://www.autotrader.co.uk/car-search?"
    mapping = search_mapping
    parts = []
    for key, value in params.items():
        if value and key in mapping:
            parts.append(mapping[key](value))
    url = base + '&'.join(parts)
    print(url)
    return url
    
    
    pass
    
if __name__ == '__main__':
    generate_autotrader_url({'make': 'Honda', 'seller_type': 'private'})