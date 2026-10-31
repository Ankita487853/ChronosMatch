
# ChronosMatch: Cython Matching Core

cpdef double calculate_match_price(
    double buy_price,
    double sell_price
):
    if buy_price >= sell_price:
        return sell_price
    return 0.0


cpdef int calculate_match_quantity(
    int buy_quantity,
    int sell_quantity
):
    if buy_quantity < sell_quantity:
        return buy_quantity
    return sell_quantity


cpdef list match_orders(
    list prices,
    list quantities,
    double incoming_price,
    int incoming_quantity,
    bint incoming_is_buy
):
    """
    Match incoming orders against resting orders.

    Returns (index, execution_price, matched_quantity).
    """

    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(prices)

    cdef double resting_price
    cdef int resting_quantity
    cdef int remaining = incoming_quantity
    cdef int matched_quantity

    cdef list trades = []

    if len(prices) != len(quantities):
        raise ValueError("Input lists must have equal lengths.")

    if incoming_quantity <= 0:
        raise ValueError("Incoming quantity must be positive.")

    for i in range(count):

        if remaining <= 0:
            break

        resting_price = prices[i]
        resting_quantity = quantities[i]

        if resting_quantity <= 0:
            continue

        if incoming_is_buy:
            if resting_price > incoming_price:
                break
        else:
            if resting_price < incoming_price:
                break

        if remaining < resting_quantity:
            matched_quantity = remaining
        else:
            matched_quantity = resting_quantity

        trades.append((
            i,
            resting_price,
            matched_quantity
        ))

        remaining -= matched_quantity
        quantities[i] = resting_quantity - matched_quantity

    return trades
