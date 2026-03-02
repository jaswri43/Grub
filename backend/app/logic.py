from fastapi import HTTPException
from app.data import load_menu
from collections import Counter

# getting the menu
def filter_menu(restaurant_id: str):
    return load_menu(restaurant_id)

# optimizing the order
def optimize_order(menu, deals, item_requirements, ingredient_requirements, available_points, delta_pct=0.3, max_results=10):
    # Convert list inputs to quantity dicts
    item_req_counts = Counter(item_requirements)
    ing_req_counts = Counter(ingredient_requirements)

    # Assign indices for items and ingredients
    all_items = list({item['slug'] for item in menu["menu"]})
    all_ingredients = list({ing for item in menu["menu"] for ing in item['ingredients']})

    item_index = {slug: i for i, slug in enumerate(all_items)}
    ing_index = {ing: i for i, ing in enumerate(all_ingredients)}

    # Convert quantity-based requirements into lists
    item_req_list = [0] * len(all_items)
    for slug, qty in item_req_counts.items():
        if slug in item_index:
            item_req_list[item_index[slug]] = qty

    ing_req_list = [0] * len(all_ingredients)
    for ing, qty in ing_req_counts.items():
        if ing in ing_index:
            ing_req_list[ing_index[ing]] = qty

    menu_items = {item['slug']: item for item in menu["menu"]}

    # Separate deals
    app_slot_deals = [d for d in deals if d.get("uses_app_slot", False)]
    non_app_deals = [d for d in deals if not d.get("uses_app_slot", False)]
    reward_deals = [d for d in deals if d.get("uses_reward_slot", False)]

    # Convert a single deal to one or more actions
    def convert_deal_to_actions(deal):
        actions = []

        if deal['type'] == "fixed_bundle":
            items = deal['items']
            cost = deal['price']
            item_counts = [0] * len(all_items)
            ing_counts = [0] * len(all_ingredients)
            for slug in items:
                if slug in item_index:
                    item_counts[item_index[slug]] += 1
                    for ing in menu_items[slug]['ingredients']:
                        ing_counts[ing_index[ing]] += 1
            actions.append({'item_counts': item_counts, 'ing_counts': ing_counts, 'cost': cost, 'reward_cost': 0, 'max_uses': 1, 'deal_id': deal.get('id')})

        elif deal['type'] == "percent_discount":
            slug = deal['item']
            if slug in menu_items:
                discounted_price = menu_items[slug]['price'] * (1 - deal['percent_off'] / 100)
                item_counts = [0] * len(all_items)
                ing_counts = [0] * len(all_ingredients)
                item_counts[item_index[slug]] = 1
                for ing in menu_items[slug]['ingredients']:
                    ing_counts[ing_index[ing]] = 1
                actions.append({'item_counts': item_counts, 'ing_counts': ing_counts, 'cost': discounted_price, 'reward_cost': 0, 'max_uses': 1, 'deal_id': deal.get('id')})

        elif deal['type'] == "bogo":
            eligible = [slug for slug in deal['eligible_items'] if slug in menu_items]
            # Create an action for each valid combination of (first, second) items
            for first in eligible:
                for second in eligible:
                    # Discount is applied to the cheaper item, full price for the expensive one
                    cost = max(menu_items[first]['price'], menu_items[second]['price']) + deal['second_item_price']
                    item_counts = [0] * len(all_items)
                    ing_counts = [0] * len(all_ingredients)
                    item_counts[item_index[first]] += 1
                    item_counts[item_index[second]] += 1
                    for ing in menu_items[first]['ingredients']:
                        ing_counts[ing_index[ing]] += 1
                    for ing in menu_items[second]['ingredients']:
                        ing_counts[ing_index[ing]] += 1
                    actions.append({'item_counts': item_counts, 'ing_counts': ing_counts, 'cost': cost, 'reward_cost': 0, 'max_uses': 1, 'deal_id': deal.get('id')})

        elif deal['type'] == "free_item":
            slug = deal['item']
            if slug in menu_items:
                item_counts = [0] * len(all_items)
                ing_counts = [0] * len(all_ingredients)
                item_counts[item_index[slug]] = 1
                for ing in menu_items[slug]['ingredients']:
                    ing_counts[ing_index[ing]] = 1
                actions.append({'item_counts': item_counts, 'ing_counts': ing_counts, 'cost': 0, 'reward_cost': deal['points_cost'], 'max_uses': 1, 'deal_id': deal.get('id')})

        return actions

    # Build actions given an optional app-slot deal
    def build_actions(active_app_deal=None):
        actions = []

        # Base menu items
        for item in menu_items.values():
            item_counts = [0] * len(all_items)
            ing_counts = [0] * len(all_ingredients)
            item_counts[item_index[item['slug']]] = 1
            for ing in item['ingredients']:
                ing_counts[ing_index[ing]] = 1
            actions.append({'item_counts': item_counts, 'ing_counts': ing_counts, 'cost': item['price'], 'reward_cost': 0, 'max_uses': float('inf'), 'deal_id': None})

        # Non-app-slot deals
        for deal in non_app_deals:
            actions.extend(convert_deal_to_actions(deal))

        # Active app-slot deal
        if active_app_deal:
            actions.extend(convert_deal_to_actions(active_app_deal))

        # Reward deals
        for deal in reward_deals:
            if deal['points_cost'] <= available_points:
                actions.extend(convert_deal_to_actions(deal))

        return actions

    # DFS + memoization
    def solve(actions, item_req_list, ing_req_list, points):
        memo = {}

        def dfs(item_remain, ing_remain, points_left):
            key = (tuple(item_remain), tuple(ing_remain), points_left)
            if key in memo:
                return memo[key]

            if all(x <= 0 for x in item_remain) and all(x <= 0 for x in ing_remain):
                return 0, []

            best_cost = float('inf')
            best_path = []

            for action in actions:
                if action['reward_cost'] > points_left:
                    continue

                helps = any(item_remain[i] > 0 and action['item_counts'][i] > 0 for i in range(len(item_remain))) or \
                        any(ing_remain[i] > 0 and action['ing_counts'][i] > 0 for i in range(len(ing_remain)))
                if not helps:
                    continue

                next_items = [max(0, item_remain[i] - action['item_counts'][i]) for i in range(len(item_remain))]
                next_ings = [max(0, ing_remain[i] - action['ing_counts'][i]) for i in range(len(ing_remain))]
                next_points = points_left - action['reward_cost']

                cost, path = dfs(next_items, next_ings, next_points)
                total_cost = action['cost'] + cost
                if total_cost < best_cost:
                    best_cost = total_cost
                    best_path = [action] + path

            memo[key] = (best_cost, best_path)
            return memo[key]

        return dfs(item_req_list, ing_req_list, points)

    # Try all app-slot deals to find the absolute minimum first
    all_app_deals = [None] + app_slot_deals
    best_total_cost = float('inf')
    best_order = []

    for app_deal in all_app_deals:
        actions = build_actions(app_deal)
        total_cost, path = solve(actions, item_req_list, ing_req_list, available_points)
        if total_cost < best_total_cost:
            best_total_cost = total_cost
            best_order = path

    # If no feasible solution found, raise
    if best_total_cost == float('inf'):
        raise HTTPException(status_code=400, detail="No feasible order found")

    # Define cutoff by percentage delta
    cutoff = best_total_cost * (1 + float(delta_pct))

    # Collector: gather all solutions with total_cost <= cutoff (bounded by max_results)
    collected = []  # list of tuples (cost, path, app_deal)

    for app_deal in all_app_deals:
        actions = build_actions(app_deal)

        def dfs_collect(item_remain, ing_remain, points_left, current_cost, path):
            # prune by cutoff
            if current_cost > cutoff:
                return

            # if satisfied, record solution
            if all(x <= 0 for x in item_remain) and all(x <= 0 for x in ing_remain):
                collected.append((current_cost, list(path), app_deal))
                return

            # try actions
            for action in actions:
                if action['reward_cost'] > points_left:
                    continue

                helps = any(item_remain[i] > 0 and action['item_counts'][i] > 0 for i in range(len(item_remain))) or \
                        any(ing_remain[i] > 0 and action['ing_counts'][i] > 0 for i in range(len(ing_remain)))
                if not helps:
                    continue

                next_items = [max(0, item_remain[i] - action['item_counts'][i]) for i in range(len(item_remain))]
                next_ings = [max(0, ing_remain[i] - action['ing_counts'][i]) for i in range(len(ing_remain))]
                next_points = points_left - action['reward_cost']
                next_cost = current_cost + action['cost']

                if next_cost > cutoff:
                    continue

                path.append(action)
                dfs_collect(next_items, next_ings, next_points, next_cost, path)
                path.pop()

                # early stop if we have collected enough candidates
                if len(collected) >= max_results * 5:
                    # keep some buffer but avoid runaway search
                    return

        dfs_collect(item_req_list, ing_req_list, available_points, 0, [])

    # Convert collected paths to unique, ranked options
    unique = {}
    options = []

    for cost, path, app_deal in collected:
        # compute total item counts across actions
        total_item_counts = [0] * len(all_items)
        deals_used = []
        for action in path:
            for i, qty in enumerate(action['item_counts']):
                total_item_counts[i] += qty
            if action.get('deal_id'):
                deals_used.append(action['deal_id'])

        # normalize deals order and uniqueness
        seen = set()
        unique_deals = []
        for d in deals_used:
            if d not in seen:
                seen.add(d)
                unique_deals.append(d)

        # dedupe by item counts + deals
        key = (tuple(total_item_counts), tuple(unique_deals))
        if key in unique:
            # keep cheapest representation
            if cost < unique[key]['total_price']:
                unique[key] = {'item_counts': total_item_counts, 'total_price': cost, 'deals': unique_deals}
        else:
            unique[key] = {'item_counts': total_item_counts, 'total_price': cost, 'deals': unique_deals}

    # Build options list and sort by cost asc, then number of items desc
    for val in unique.values():
        items_list = []
        for i, cnt in enumerate(val['item_counts']):
            items_list.extend([all_items[i]] * cnt)
        options.append({'optimized_items': items_list, 'total_price': round(val['total_price'], 2), 'deals_used': val['deals'], 'num_items': sum(val['item_counts'])})

    options.sort(key=lambda o: (o['total_price'], -o['num_items']))

    # limit results to max_results
    options = options[:max_results]

    # If nothing found (shouldn't happen because best_total_cost exists), fallback to best
    if not options:
        optimized_items = []
        deals_used = []
        for action in best_order:
            for i, qty in enumerate(action['item_counts']):
                optimized_items.extend([all_items[i]] * qty)
            if action.get('deal_id'):
                deals_used.append(action['deal_id'])
        seen = set()
        unique_deals = []
        for d in deals_used:
            if d not in seen:
                seen.add(d)
                unique_deals.append(d)
        return [{'optimized_items': optimized_items, 'total_price': round(best_total_cost, 2), 'deals_used': unique_deals}]

    # strip helper fields before returning
    for o in options:
        o.pop('num_items', None)

    return options