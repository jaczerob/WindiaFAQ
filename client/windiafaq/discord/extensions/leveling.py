from discord.ext import commands

import math
import random
import statistics

from windiafaq.discord.bot import WindiaFAQ
from windiafaq.discord.context import Context


def rand_stat(base: int) -> int:
	limit: int = min(base, 10000)
	pool_size: int = (limit * (limit + 1) // 2) + limit
	randomized: int = random.randint(0, pool_size)
	stat: int = 0

	if randomized >= limit:
		randomized -= limit
		stat = 1 + int(math.floor((-1 + math.sqrt((8 * randomized) + 1)) // 2))

	return stat


# Returns array:
# [0] = result of this simulation
# [1] = upper bound of stat gain for this
def calc_stat(base: int, is_attack: bool) -> list:
	if base == 0:
		return [ 0, 0 ]

	randomized_result: int = 0
	stat_modifier: float = 2.1 if not is_attack else 4.2
	max_result: int = int(1 + (base / (stat_modifier * 1.05)))

	for _ in range(100):
		randomized_result = rand_stat(max_result)

		if randomized_result > 0:
			break

	return [ randomized_result, max_result + 1 ]


# Returns array:
# [0] = total stat gained until we reach level_until
# [1] = highest possible stat
# [2] = list of all stat gains (every "gain" is a list)
def simulate_levels(base: int, is_attack: bool, level_until: int = 7) -> list:
	leveling_gains: list = []
	best_possible: int = base

	for _ in range(level_until - 1):
		gain: list = calc_stat(base, is_attack)
		leveling_gains.append(gain)
		base += gain[0]
		best_possible += calc_stat(best_possible, is_attack)[1]

	return [ base, best_possible, leveling_gains ]


# Simulates @simulations times, retrns mean of all results
def get_average(base: int, is_attack: bool, level_until: int = 7, simulations = 100) -> int:
	_sum: list = []

	for _ in range(simulations):
		_sum.append(simulate_levels(base, is_attack, level_until)[0])

	return int(statistics.mean(_sum))


class Leveling(commands.Cog):
	def __init__(self, bot: WindiaFAQ) -> None:
		self.bot = bot

	async def cog_check(self, ctx: Context) -> bool:
		if ctx.in_dm:
			return True

		if not ctx.in_lossdia or ctx.in_bot_channel:
			return True

		return ctx.is_owner or ctx.is_moderator

	@commands.command(
		name="leveling",
		description="Displays stat gain boundaries and simulated averages for item leveling, based on input of stats at level 1 (flames/starforce excluded).",
		usage="<stat> <attack>",
	)
	async def _level(self, ctx: Context, main_stat: int, attack: int):
		highest_possible_stat_lv5: int = simulate_levels(main_stat, False, 5)[1]
		average_stat_lv5: int = get_average(main_stat, False, 5)
		highest_possible_att_lv5: int = simulate_levels(attack, True, 5)[1]
		average_att_lv5: int = get_average(attack, True, 5)
		lv7_simulation_stat = simulate_levels(main_stat, False, 7)
		highest_possible_stat_lv7: int = lv7_simulation_stat[1]
		average_stat_lv7: int = get_average(main_stat, False, 7)
		lv7_simulation_att = simulate_levels(attack, True, 7)
		highest_possible_att_lv7: int = lv7_simulation_att[1]
		average_att_lv7: int = get_average(attack, True, 7)

		cur_stat = main_stat
		cur_att = attack

		simulated = str()

		for x in range(6):
			cur_stat += lv7_simulation_stat[2][x][0]
			cur_att += lv7_simulation_att[2][x][0]
			simulated += f"- Lv. {x + 2}: stat +{lv7_simulation_stat[2][x][0]} (max: {lv7_simulation_stat[2][x][1]}) (now: {cur_stat}), att +{lv7_simulation_att[2][x][0]} (max: {lv7_simulation_att[2][x][1]}) (now: {cur_att})\n"

		await ctx.reply(f"""Base: Stat {main_stat}, att {attack}
Highest possible stats @ level 5 (stat: {highest_possible_stat_lv5}, att: {highest_possible_att_lv5})
Average @ level 5 (stat: {average_stat_lv5}, att: {average_att_lv5})
Highest possible stats @ level 7 (stat: {highest_possible_stat_lv7}, att: {highest_possible_att_lv7})
Average @ level 7 (stat: {average_stat_lv7}, att: {average_att_lv7})\n
Simulation:
```
{simulated.strip()}
```""")

async def setup(bot) -> None:
	await bot.add_cog(Leveling(bot))