from app.core.pricing_constants import (
    PRICE_PER_1K_INPUT, PRICE_PER_1K_CACHED_INPUT, PRICE_PER_1K_OUTPUT
)



def calculate_cost_cents(input_tokens:int,cached_input_tokens:int,reasoning_tokens:int,output_tokens:int)->int:

    input_cost = (input_tokens/1000)*PRICE_PER_1K_INPUT
    cached_cost = (cached_input_tokens/1000)*PRICE_PER_1K_CACHED_INPUT

    # Reasoning tokens are billed at the output rate
    
    output_cost = ((output_tokens+reasoning_tokens)/1000) * PRICE_PER_1K_OUTPUT

    total=input_cost + cached_cost + output_cost

    total=total*100

    return round(total)

