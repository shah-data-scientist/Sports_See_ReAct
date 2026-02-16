"""
FILE: test_data.py
STATUS: Active
RESPONSIBILITY: All evaluation test cases in unified format (206 total)
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Shahu

STRUCTURE:
- ALL_TEST_CASES: List of 206 UnifiedTestCase instances
  - 80 SQL test cases
  - 75 Vector test cases
  - 51 Hybrid test cases

CHANGES (2026-02-15):
- Renamed: ground_truth → ground_truth_vector
- Removed: ground_truth_answer (will be generated dynamically by judge LLM)
- Removed: min_vector_sources (unused - info in ground_truth_vector)
- Removed: expected_source_types (unused - info in ground_truth_vector)
- Judge LLM generates expected answer from ground_truth_data and ground_truth_vector
"""

import logging
from evaluation.models import UnifiedTestCase, TestType

logger = logging.getLogger(__name__)

# ============================================================================
# ALL TEST CASES (206 total)
# ============================================================================

ALL_TEST_CASES = [
    UnifiedTestCase(
        question='Who scored the most points this season?',
        test_type=TestType.SQL,
        category='simple_sql_top_n',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1',
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'pts': 2485},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who are the top 3 rebounders in the league?',
        test_type=TestType.SQL,
        category='simple_sql_top_n',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.reb DESC LIMIT 3',
        ground_truth_data=[{'name': 'Ivica Zubac', 'reb': 1008}, {'name': 'Domantas Sabonis', 'reb': 973}, {'name': 'Karl-Anthony Towns', 'reb': 922}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who are the top 5 players in steals?',
        test_type=TestType.SQL,
        category='simple_sql_top_n',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.stl FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.stl DESC LIMIT 5',
        ground_truth_data=[{'name': 'Dyson Daniels', 'stl': 228}, {'name': 'Shai Gilgeous-Alexander', 'stl': 129}, {'name': 'Nikola Jokić', 'stl': 126}, {'name': 'Kris Dunn', 'stl': 126}, {'name': 'Cason Wallace', 'stl': 122}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who has the best free throw percentage?',
        test_type=TestType.SQL,
        category='simple_sql_top_n',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ft_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ft_pct IS NOT NULL ORDER BY ps.ft_pct DESC LIMIT 1',
        ground_truth_data={'name': 'Sam Hauser', 'ft_pct': 100.0},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who has the highest true shooting percentage?',
        test_type=TestType.SQL,
        category='simple_sql_top_n',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ts_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ts_pct IS NOT NULL AND ps.gp > 20 ORDER BY ps.ts_pct DESC LIMIT 1',
        ground_truth_data={'name': 'Kai Jones', 'ts_pct': 80.4},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What is LeBron James' average points per game?",
        test_type=TestType.SQL,
        category='simple_sql_player_stats',

        # SQL Expectations
        expected_sql="SELECT p.name, ROUND(ps.pts*1.0/ps.gp, 1) as ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%LeBron%'",
        ground_truth_data={'name': 'LeBron James', 'ppg': 24.4},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What is Stephen Curry's 3-point percentage?",
        test_type=TestType.SQL,
        category='simple_sql_player_stats',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Stephen Curry%'",
        ground_truth_data={'name': 'Stephen Curry', 'three_pct': 39.7},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What is Nikola Jokić's total rebounds?",
        test_type=TestType.SQL,
        category='simple_sql_player_stats',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Jokić%'",
        ground_truth_data={'name': 'Nikola Jokić', 'reb': 889},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How many assists did Chris Paul record?',
        test_type=TestType.SQL,
        category='simple_sql_player_stats',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Chris Paul%'",
        ground_truth_data={'name': 'Chris Paul', 'ast': 607},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How many players on the Lakers roster?',
        test_type=TestType.SQL,
        category='simple_sql_team_roster',

        # SQL Expectations
        expected_sql="SELECT COUNT(*) as player_count FROM players WHERE team_abbr = 'LAL'",
        ground_truth_data={'player_count': 20},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='List all players on the Golden State Warriors.',
        test_type=TestType.SQL,
        category='simple_sql_team_roster',

        # SQL Expectations
        expected_sql="SELECT name FROM players WHERE team_abbr = 'GSW' ORDER BY name",
        ground_truth_data=[{'name': 'Brandin Podziemski'}, {'name': 'Braxton Key'}, {'name': 'Buddy Hield'}, {'name': 'Draymond Green'}, {'name': 'Gary Payton II'}, {'name': 'Gui Santos'}, {'name': 'Jackson Rowe'}, {'name': 'Jimmy Butler III'}, {'name': 'Jonathan Kuminga'}, {'name': 'Kevin Knox II'}, {'name': 'Kevon Looney'}, {'name': 'Moses Moody'}, {'name': 'Pat Spencer'}, {'name': 'Quinten Post'}, {'name': 'Stephen Curry'}, {'name': 'Trayce Jackson-Davis'}, {'name': 'Yuri Collins'}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which player has the most wins this season?',
        test_type=TestType.SQL,
        category='simple_sql_top_n',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.w FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.w DESC LIMIT 1',
        ground_truth_data={'name': 'Jarrett Allen', 'w': 64},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the average player age in the NBA?',
        test_type=TestType.SQL,
        category='aggregation_sql_league',

        # SQL Expectations
        expected_sql='SELECT AVG(age) as avg_age FROM players WHERE age IS NOT NULL',
        ground_truth_data={'avg_age': 26.2},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Compare Jokić and Embiid's stats",
        test_type=TestType.SQL,
        category='comparison_sql_players',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Nikola Jokić', 'Joel Embiid')",
        ground_truth_data=[{'name': 'Nikola Jokić', 'pts': 2072, 'reb': 889, 'ast': 714}, {'name': 'Joel Embiid', 'pts': 452, 'reb': 156, 'ast': 86}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who shoots better from 3, Curry or Lillard?',
        test_type=TestType.SQL,
        category='comparison_sql_players',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Stephen Curry', 'Damian Lillard') ORDER BY ps.three_pct DESC",
        ground_truth_data=[{'name': 'Stephen Curry', 'three_pct': 39.7}, {'name': 'Damian Lillard', 'three_pct': 37.6}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who is more efficient goal maker, Jokić or Embiid?',
        test_type=TestType.SQL,
        category='comparison_sql_players',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.fg_pct, ps.efg_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Nikola Jokić', 'Joel Embiid') ORDER BY ps.fg_pct DESC",
        ground_truth_data=[{'name': 'Nikola Jokić', 'fg_pct': 57.6, 'efg_pct': 62.7}, {'name': 'Joel Embiid', 'fg_pct': 44.4, 'efg_pct': 48.1}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare Jayson Tatum and Kevin Durant scoring efficiency',
        test_type=TestType.SQL,
        category='comparison_sql_players',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.fg_pct, ps.efg_pct, ps.ts_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Jayson Tatum', 'Kevin Durant') ORDER BY ps.pts DESC",
        ground_truth_data=[{'name': 'Jayson Tatum', 'pts': 1930, 'fg_pct': 45.2, 'efg_pct': 53.7, 'ts_pct': 58.2}, {'name': 'Kevin Durant', 'pts': 1649, 'fg_pct': 52.7, 'efg_pct': 59.8, 'ts_pct': 64.2}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who has more assists, James Harden or Chris Paul?',
        test_type=TestType.SQL,
        category='comparison_sql_players',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Harden%' OR p.name LIKE '%Chris Paul%' ORDER BY ps.ast DESC LIMIT 2",
        ground_truth_data=[{'name': 'James Harden', 'ast': 687}, {'name': 'Chris Paul', 'ast': 607}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare the top 2 steals leaders',
        test_type=TestType.SQL,
        category='comparison_sql_players',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.stl FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.stl DESC LIMIT 2',
        ground_truth_data=[{'name': 'Dyson Daniels', 'stl': 228}, {'name': 'Shai Gilgeous-Alexander', 'stl': 129}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare blocks between the top 2 leaders',
        test_type=TestType.SQL,
        category='comparison_sql_players',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.blk FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.blk DESC LIMIT 2',
        ground_truth_data=[{'name': 'Victor Wembanyama', 'blk': 175}, {'name': 'Brook Lopez', 'blk': 152}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='What is the average 3-point percentage for all players?',
        test_type=TestType.SQL,
        category='aggregation_sql_league',

        # SQL Expectations
        expected_sql='SELECT AVG(three_pct) as avg_3p_pct FROM player_stats WHERE three_pct IS NOT NULL',
        ground_truth_data={'avg_3p_pct': 29.9},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the average field goal percentage in the league?',
        test_type=TestType.SQL,
        category='aggregation_sql_league',

        # SQL Expectations
        expected_sql='SELECT ROUND(AVG(fg_pct), 1) as avg_fg_pct FROM player_stats WHERE fg_pct IS NOT NULL',
        ground_truth_data={'avg_fg_pct': 44.6},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the average PIE in the league?',
        test_type=TestType.SQL,
        category='aggregation_sql_league',

        # SQL Expectations
        expected_sql='SELECT ROUND(AVG(pie), 1) as avg_pie FROM player_stats WHERE pie IS NOT NULL',
        ground_truth_data={'avg_pie': 8.9},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the average rebounds per game league-wide?',
        test_type=TestType.SQL,
        category='aggregation_sql_league',

        # SQL Expectations
        expected_sql='SELECT AVG(CAST(reb AS REAL) / gp) as avg_rpg FROM player_stats WHERE gp > 0',
        ground_truth_data={'avg_rpg': 3.6},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How many players scored over 1000 points?',
        test_type=TestType.SQL,
        category='aggregation_sql_count',

        # SQL Expectations
        expected_sql='SELECT COUNT(*) as player_count FROM player_stats WHERE pts > 1000',
        ground_truth_data={'player_count': 84},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How many players have a true shooting percentage over 60%?',
        test_type=TestType.SQL,
        category='aggregation_sql_count',

        # SQL Expectations
        expected_sql='SELECT COUNT(*) as player_count FROM player_stats WHERE ts_pct > 60 AND gp >= 20',
        ground_truth_data={'player_count': 118},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How many players have more than 500 assists?',
        test_type=TestType.SQL,
        category='aggregation_sql_count',

        # SQL Expectations
        expected_sql='SELECT COUNT(*) as count FROM player_stats WHERE ast > 500',
        ground_truth_data={'count': 10},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How many players played more than 50 games?',
        test_type=TestType.SQL,
        category='aggregation_sql_count',

        # SQL Expectations
        expected_sql='SELECT COUNT(*) as count FROM player_stats WHERE gp > 50',
        ground_truth_data={'count': 282},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the highest PIE in the league?',
        test_type=TestType.SQL,
        category='aggregation_sql_league',

        # SQL Expectations
        expected_sql='SELECT MAX(pie) as max_pie FROM player_stats',
        ground_truth_data={'max_pie': 40.0},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the maximum number of blocks recorded by any player?',
        test_type=TestType.SQL,
        category='aggregation_sql_league',

        # SQL Expectations
        expected_sql='SELECT MAX(blk) as max_blocks FROM player_stats',
        ground_truth_data={'max_blocks': 175},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='What is the average field goal percentage for the Lakers?',
        test_type=TestType.SQL,
        category='aggregation_sql_team',

        # SQL Expectations
        expected_sql="SELECT ROUND(AVG(ps.fg_pct), 1) as avg_fg_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'LAL' AND ps.fg_pct IS NOT NULL",
        ground_truth_data={'avg_fg_pct': 44.6},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which players score more points per game than the league average?',
        test_type=TestType.SQL,
        category='complex_sql_subquery',

        # SQL Expectations
        expected_sql='SELECT p.name, ROUND(ps.pts*1.0/ps.gp, 1) as ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 0 AND ps.pts*1.0/ps.gp > (SELECT AVG(pts*1.0/gp) FROM player_stats WHERE gp > 0) ORDER BY ppg DESC LIMIT 5',
        ground_truth_data=[{'name': 'Shai Gilgeous-Alexander', 'ppg': 32.7}, {'name': 'Giannis Antetokounmpo', 'ppg': 30.4}, {'name': 'Nikola Jokić', 'ppg': 29.6}, {'name': 'Luka Dončić', 'ppg': 28.2}, {'name': 'Anthony Edwards', 'ppg': 27.6}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Find players with both high scoring (1500+ points) and high assists (300+ assists)',
        test_type=TestType.SQL,
        category='complex_sql_multiple_conditions',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts >= 1500 AND ps.ast >= 300 ORDER BY ps.pts DESC LIMIT 4',
        ground_truth_data=[{'name': 'Shai Gilgeous-Alexander', 'pts': 2485, 'ast': 486}, {'name': 'Anthony Edwards', 'pts': 2180, 'ast': 356}, {'name': 'Nikola Jokić', 'pts': 2072, 'ast': 714}, {'name': 'Giannis Antetokounmpo', 'pts': 2037, 'ast': 436}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which players have better than 50% field goal percentage AND 35%+ from three?',
        test_type=TestType.SQL,
        category='complex_sql_multiple_conditions',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.fg_pct, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.fg_pct >= 50 AND ps.three_pct >= 35 AND ps.gp >= 50 ORDER BY ps.fg_pct DESC LIMIT 5',
        ground_truth_data=[{'name': 'Dwight Powell', 'fg_pct': 68.9, 'three_pct': 40.0}, {'name': 'Drew Eubanks', 'fg_pct': 59.3, 'three_pct': 50.0}, {'name': 'Domantas Sabonis', 'fg_pct': 59.0, 'three_pct': 41.7}, {'name': 'Christian Braun', 'fg_pct': 58.0, 'three_pct': 39.7}, {'name': 'Nikola Jokić', 'fg_pct': 57.6, 'three_pct': 41.7}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Find players averaging double-digits in points, rebounds, and assists',
        test_type=TestType.SQL,
        category='complex_sql_calculated_triple_condition',

        # SQL Expectations
        expected_sql='SELECT p.name, ROUND(ps.pts*1.0/ps.gp, 1) as ppg, ROUND(ps.reb*1.0/ps.gp, 1) as rpg, ROUND(ps.ast*1.0/ps.gp, 1) as apg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 0 AND ps.pts*1.0/ps.gp >= 10 AND ps.reb*1.0/ps.gp >= 10 AND ps.ast*1.0/ps.gp >= 10',
        ground_truth_data=[{'name': 'Nikola Jokić', 'ppg': 29.6, 'rpg': 12.7, 'apg': 10.2}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Find the top 5 players by total defensive actions (steals + blocks)',
        test_type=TestType.SQL,
        category='complex_sql_calculated_field',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.stl, ps.blk, (ps.stl + ps.blk) as defensive_actions FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY (ps.stl + ps.blk) DESC LIMIT 5',
        ground_truth_data=[{'name': 'Dyson Daniels', 'stl': 228, 'blk': 53, 'defensive_actions': 281}, {'name': 'Victor Wembanyama', 'stl': 51, 'blk': 175, 'defensive_actions': 226}, {'name': 'Shai Gilgeous-Alexander', 'stl': 129, 'blk': 76, 'defensive_actions': 205}, {'name': 'Myles Turner', 'stl': 58, 'blk': 144, 'defensive_actions': 202}, {'name': 'Jaren Jackson Jr,', 'stl': 89, 'blk': 111, 'defensive_actions': 200}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which players have the best assist-to-turnover ratio among those with 300+ assists?',
        test_type=TestType.SQL,
        category='complex_sql_ratio_calculation',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ast, ps.tov, ROUND(ps.ast*1.0/ps.tov, 2) as ast_to_ratio FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ast >= 300 AND ps.tov > 0 ORDER BY (ps.ast*1.0/ps.tov) DESC LIMIT 5',
        ground_truth_data=[{'name': 'Tyrese Haliburton', 'ast': 672, 'tov': 117, 'ast_to_ratio': 5.74}, {'name': 'Tyus Jones', 'ast': 429, 'tov': 89, 'ast_to_ratio': 4.82}, {'name': 'Chris Paul', 'ast': 607, 'tov': 131, 'ast_to_ratio': 4.63}, {'name': 'Mike Conley', 'ast': 320, 'tov': 78, 'ast_to_ratio': 4.1}, {'name': 'Fred VanVleet', 'ast': 336, 'tov': 90, 'ast_to_ratio': 3.73}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What percentage of players have a true shooting percentage above 60%?',
        test_type=TestType.SQL,
        category='complex_sql_percentage_calculation',

        # SQL Expectations
        expected_sql='SELECT ROUND(100.0 * COUNT(CASE WHEN ts_pct > 60 THEN 1 END) / COUNT(*), 1) as pct_above_60 FROM player_stats WHERE ts_pct IS NOT NULL AND gp >= 20',
        ground_truth_data={'pct_above_60': 25.9},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who are the most efficient scorers among players with 50+ games played?',
        test_type=TestType.SQL,
        category='complex_sql_filtering',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.efg_pct, ps.pts, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp >= 50 AND ps.efg_pct IS NOT NULL ORDER BY ps.efg_pct DESC LIMIT 5',
        ground_truth_data=[{'name': 'Jaxson Hayes', 'efg_pct': 72.2}, {'name': 'Jarrett Allen', 'efg_pct': 70.6}, {'name': 'Dwight Powell', 'efg_pct': 70.5}, {'name': 'Adem Bona', 'efg_pct': 70.3}, {'name': 'Daniel Gafford', 'efg_pct': 70.2}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who are the top 3 players in points per game among those who played at least 70 games?',
        test_type=TestType.SQL,
        category='complex_sql_filtering_calculation',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.gp, ROUND(ps.pts*1.0/ps.gp, 1) as ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp >= 70 ORDER BY (ps.pts*1.0/ps.gp) DESC LIMIT 3',
        ground_truth_data=[{'name': 'Shai Gilgeous-Alexander', 'pts': 2485, 'gp': 76, 'ppg': 32.7}, {'name': 'Nikola Jokić', 'pts': 2072, 'gp': 70, 'ppg': 29.6}, {'name': 'Anthony Edwards', 'pts': 2180, 'gp': 79, 'ppg': 27.6}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Find the most versatile players with at least 1000 points, 400 rebounds, and 200 assists',
        test_type=TestType.SQL,
        category='complex_sql_versatility',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts >= 1000 AND ps.reb >= 400 AND ps.ast >= 200 ORDER BY (ps.pts + ps.reb + ps.ast) DESC LIMIT 5',
        ground_truth_data=[{'name': 'Nikola Jokić', 'pts': 2072, 'reb': 889, 'ast': 714}, {'name': 'Giannis Antetokounmpo', 'pts': 2037, 'reb': 797, 'ast': 436}, {'name': 'Jayson Tatum', 'pts': 1930, 'reb': 626, 'ast': 432}, {'name': 'Anthony Edwards', 'pts': 2180, 'reb': 450, 'ast': 356}, {'name': 'James Harden', 'pts': 1801, 'reb': 458, 'ast': 687}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which team has the highest average points per player?',
        test_type=TestType.SQL,
        category='complex_sql_group_by',

        # SQL Expectations
        expected_sql='SELECT p.team_abbr, ROUND(AVG(ps.pts), 1) as avg_pts FROM players p JOIN player_stats ps ON p.id = ps.player_id GROUP BY p.team_abbr ORDER BY avg_pts DESC LIMIT 5',
        ground_truth_data=[{'team_abbr': 'DEN', 'avg_pts': 582.3}, {'team_abbr': 'SAS', 'avg_pts': 566.6}, {'team_abbr': 'CLE', 'avg_pts': 565.6}, {'team_abbr': 'BOS', 'avg_pts': 561.8}, {'team_abbr': 'OKC', 'avg_pts': 548.9}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare the average points per player between the Celtics and Lakers',
        test_type=TestType.SQL,
        category='complex_sql_team_comparison',

        # SQL Expectations
        expected_sql="SELECT p.team_abbr, ROUND(AVG(ps.pts), 1) as avg_pts, COUNT(*) as player_count FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr IN ('BOS', 'LAL') GROUP BY p.team_abbr ORDER BY avg_pts DESC",
        ground_truth_data=[{'team_abbr': 'BOS', 'avg_pts': 561.8, 'player_count': 17}, {'team_abbr': 'LAL', 'avg_pts': 434.6, 'player_count': 20}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which teams have at least 3 players with more than 1000 points?',
        test_type=TestType.SQL,
        category='complex_sql_having',

        # SQL Expectations
        expected_sql='SELECT p.team_abbr, COUNT(*) as high_scorers FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 1000 GROUP BY p.team_abbr HAVING COUNT(*) >= 3 ORDER BY high_scorers DESC LIMIT 5',
        ground_truth_data=[{'team_abbr': 'SAS', 'high_scorers': 5}, {'team_abbr': 'NYK', 'high_scorers': 5}, {'team_abbr': 'CLE', 'high_scorers': 5}, {'team_abbr': 'SAC', 'high_scorers': 4}, {'team_abbr': 'IND', 'high_scorers': 4}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Find players between 25 and 30 years old with more than 1500 points',
        test_type=TestType.SQL,
        category='complex_sql_range',

        # SQL Expectations
        expected_sql='SELECT p.name, p.age, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.age BETWEEN 25 AND 30 AND ps.pts > 1500 ORDER BY ps.pts DESC LIMIT 5',
        ground_truth_data=[{'name': 'Shai Gilgeous-Alexander', 'age': 26, 'pts': 2485}, {'name': 'Nikola Jokić', 'age': 30, 'pts': 2072}, {'name': 'Giannis Antetokounmpo', 'age': 30, 'pts': 2037}, {'name': 'Jayson Tatum', 'age': 27, 'pts': 1930}, {'name': 'Devin Booker', 'age': 28, 'pts': 1920}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Show me the top scorer',
        test_type=TestType.SQL,
        category='conversational_initial',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1',
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'pts': 2485},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Who's the best rebounder?",
        test_type=TestType.SQL,
        category='conversational_casual',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.reb DESC LIMIT 1',
        ground_truth_data={'name': 'Ivica Zubac', 'reb': 1008},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Tell me about LeBron's stats",
        test_type=TestType.SQL,
        category='conversational_casual',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%LeBron%'",
        ground_truth_data={'name': 'LeBron James', 'pts': 1708, 'reb': 546, 'ast': 574},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='gimme the assist leaders plz',
        test_type=TestType.SQL,
        category='conversational_casual',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.ast DESC LIMIT 5',
        ground_truth_data=[{'name': 'Trae Young', 'ast': 882}, {'name': 'Nikola Jokić', 'ast': 714}, {'name': 'James Harden', 'ast': 687}, {'name': 'Tyrese Haliburton', 'ast': 672}, {'name': 'Cade Cunningham', 'ast': 637}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What about his assists?',
        test_type=TestType.SQL,
        category='conversational_followup',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Shai%'",
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'ast': 486},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='How many games did he play?',
        test_type=TestType.SQL,
        category='conversational_followup',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Zubac%'",
        ground_truth_data={'name': 'Ivica Zubac', 'gp': 80},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare him to Curry',
        test_type=TestType.SQL,
        category='conversational_comparison',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('LeBron James', 'Stephen Curry')",
        ground_truth_data=[{'name': 'LeBron James', 'pts': 1708, 'reb': 546, 'ast': 574}, {'name': 'Stephen Curry', 'pts': 1715, 'reb': 308, 'ast': 420}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which of them plays for the Hawks?',
        test_type=TestType.SQL,
        category='conversational_filter_followup',

        # SQL Expectations
        expected_sql="SELECT p.name, p.team_abbr, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'ATL' ORDER BY ps.ast DESC LIMIT 1",
        ground_truth_data={'name': 'Trae Young', 'ast': 882},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Show me the pts leaders this season',
        test_type=TestType.SQL,
        category='conversational_stat_abbreviation',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 5',
        ground_truth_data=[{'name': 'Shai Gilgeous-Alexander', 'pts': 2485}, {'name': 'Anthony Edwards', 'pts': 2180}, {'name': 'Nikola Jokić', 'pts': 2072}, {'name': 'Giannis Antetokounmpo', 'pts': 2037}, {'name': 'Jayson Tatum', 'pts': 1930}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who is the MVP this season?',
        test_type=TestType.SQL,
        category='conversational_ambiguous',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pie, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 ORDER BY ps.pie DESC LIMIT 1',
        ground_truth_data={'name': 'Giannis Antetokounmpo', 'pie': 21.0, 'pts': 2037},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Show me players with good three-point shooting',
        test_type=TestType.SQL,
        category='conversational_progressive_filtering',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.three_pct > 38 AND ps.gp >= 50 ORDER BY ps.three_pct DESC LIMIT 5',
        ground_truth_data=[{'name': 'Drew Eubanks', 'three_pct': 50.0}, {'name': 'Seth Curry', 'three_pct': 45.6}, {'name': 'Zach LaVine', 'three_pct': 44.6}, {'name': 'Ty Jerome', 'three_pct': 43.9}, {'name': 'Taurean Prince', 'three_pct': 43.9}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='progressive_filtering_1',
    ),
    UnifiedTestCase(
        question='Only from the Lakers',
        test_type=TestType.SQL,
        category='conversational_progressive_filtering',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'LAL' AND ps.three_pct IS NOT NULL ORDER BY ps.three_pct DESC LIMIT 5",
        ground_truth_data=[{'name': 'Rui Hachimura', 'three_pct': 41.3}, {'name': 'Dorian Finney-Smith', 'three_pct': 41.1}, {'name': 'Jordan Goodwin', 'three_pct': 38.2}, {'name': 'Austin Reaves', 'three_pct': 37.7}, {'name': 'LeBron James', 'three_pct': 37.6}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='progressive_filtering_1',
    ),
    UnifiedTestCase(
        question='Sort them by attempts',
        test_type=TestType.SQL,
        category='conversational_progressive_filtering',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.three_pct, ps.three_pa FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'LAL' AND ps.three_pct IS NOT NULL ORDER BY ps.three_pa DESC LIMIT 5",
        ground_truth_data=[{'name': 'Austin Reaves', 'three_pct': 37.7, 'three_pa': 533}, {'name': 'Luka Dončić', 'three_pct': 36.8, 'three_pa': 480}, {'name': 'LeBron James', 'three_pct': 37.6, 'three_pa': 399}, {'name': 'Dalton Knecht', 'three_pct': 37.6, 'three_pa': 343}, {'name': 'Dorian Finney-Smith', 'three_pct': 41.1, 'three_pa': 315}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='progressive_filtering_1',
    ),
    UnifiedTestCase(
        question='Show me stats for the Warriors',
        test_type=TestType.SQL,
        category='conversational_correction',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'GSW' ORDER BY ps.pts DESC LIMIT 3",
        ground_truth_data=[{'name': 'Stephen Curry', 'pts': 1715, 'reb': 308, 'ast': 420}, {'name': 'Jimmy Butler III', 'pts': 963, 'reb': 297, 'ast': 297}, {'name': 'Buddy Hield', 'pts': 910, 'reb': 262, 'ast': 131}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='correction_celtics',
    ),
    UnifiedTestCase(
        question='Actually, I meant the Celtics',
        test_type=TestType.SQL,
        category='conversational_correction',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'BOS' ORDER BY ps.pts DESC LIMIT 3",
        ground_truth_data=[{'name': 'Jayson Tatum', 'pts': 1930, 'reb': 626, 'ast': 432}, {'name': 'Jaylen Brown', 'pts': 1399, 'reb': 365, 'ast': 284}, {'name': 'Derrick White', 'pts': 1246, 'reb': 342, 'ast': 365}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='correction_celtics',
    ),

    UnifiedTestCase(
        question='Who is their top scorer?',
        test_type=TestType.SQL,
        category='conversational_correction',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'BOS' ORDER BY ps.pts DESC LIMIT 1",
        ground_truth_data={'name': 'Jayson Tatum', 'pts': 1930},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='correction_celtics',
    ),
    UnifiedTestCase(
        question='Who leads in steals?',
        test_type=TestType.SQL,
        category='conversational_implicit_continuation',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.stl FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.stl DESC LIMIT 1',
        ground_truth_data={'name': 'Dyson Daniels', 'stl': 228},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='stats_continuation',
    ),
    UnifiedTestCase(
        question='And blocks?',
        test_type=TestType.SQL,
        category='conversational_implicit_continuation',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.blk FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.blk DESC LIMIT 1',
        ground_truth_data={'name': 'Victor Wembanyama', 'blk': 175},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='stats_continuation',
    ),
    UnifiedTestCase(
        question='What about turnovers?',
        test_type=TestType.SQL,
        category='conversational_implicit_continuation',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.tov FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.tov DESC LIMIT 1',
        ground_truth_data={'name': 'Trae Young', 'tov': 357},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='stats_continuation',
    ),
    UnifiedTestCase(
        question="Tell me about Jayson Tatum's scoring",
        test_type=TestType.SQL,
        category='conversational_multi_entity',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.gp, ROUND(ps.pts*1.0/ps.gp, 1) as ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Tatum%'",
        ground_truth_data={'name': 'Jayson Tatum', 'pts': 1930, 'gp': 72, 'ppg': 26.8},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='multi_entity_tatum_lebron',
    ),
    UnifiedTestCase(
        question='How does LeBron James compare?',
        test_type=TestType.SQL,
        category='conversational_multi_entity',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.gp, ROUND(ps.pts*1.0/ps.gp, 1) as ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Jayson Tatum', 'LeBron James')",
        ground_truth_data=[{'name': 'Jayson Tatum', 'pts': 1930, 'gp': 72, 'ppg': 26.8}, {'name': 'LeBron James', 'pts': 1708, 'gp': 70, 'ppg': 24.4}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='multi_entity_tatum_lebron',
    ),
    UnifiedTestCase(
        question='Between the two, who has more rebounds?',
        test_type=TestType.SQL,
        category='conversational_multi_entity',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Jayson Tatum', 'LeBron James') ORDER BY ps.reb DESC",
        ground_truth_data=[{'name': 'Jayson Tatum', 'reb': 626}, {'name': 'LeBron James', 'reb': 546}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='multi_entity_tatum_lebron',
    ),
    UnifiedTestCase(
        question='Which team has the highest total points?',
        test_type=TestType.SQL,
        category='conversational_team_pronoun',

        # SQL Expectations
        expected_sql='SELECT p.team_abbr, SUM(ps.pts) as total_pts FROM players p JOIN player_stats ps ON p.id = ps.player_id GROUP BY p.team_abbr ORDER BY total_pts DESC LIMIT 1',
        ground_truth_data={'team_abbr': 'DET', 'total_pts': 10292},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='team_pronoun_pistons',
    ),
    UnifiedTestCase(
        question='Who are their top scorers?',
        test_type=TestType.SQL,
        category='conversational_team_pronoun',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'DET' ORDER BY ps.pts DESC LIMIT 3",
        ground_truth_data=[{'name': 'Cade Cunningham', 'pts': 1827}, {'name': 'Malik Beasley', 'pts': 1337}, {'name': 'Tobias Harris', 'pts': 1000}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='team_pronoun_pistons',
    ),
    UnifiedTestCase(
        question='What is the average age of their players?',
        test_type=TestType.SQL,
        category='conversational_team_pronoun',

        # SQL Expectations
        expected_sql="SELECT ROUND(AVG(p.age), 1) as avg_age FROM players p WHERE p.team_abbr = 'DET' AND p.age IS NOT NULL",
        ground_truth_data={'avg_age': 25.3},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='team_pronoun_pistons',
    ),

    UnifiedTestCase(
        question='whos got da most pts this szn',
        test_type=TestType.SQL,
        category='noisy_sql_typo',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1',
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'pts': 2485},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='show me currys 3 pt pct',
        test_type=TestType.SQL,
        category='noisy_sql_abbreviation',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Stephen Curry%'",
        ground_truth_data={'name': 'Stephen Curry', 'three_pct': 39.7},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='how many playas got more than 1k points??',
        test_type=TestType.SQL,
        category='noisy_sql_slang',

        # SQL Expectations
        expected_sql='SELECT COUNT(*) as player_count FROM player_stats WHERE pts > 1000',
        ground_truth_data={'player_count': 84},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='jokic rebounds total plzz',
        test_type=TestType.SQL,
        category='noisy_sql_informal',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Jokić%'",
        ground_truth_data={'name': 'Nikola Jokić', 'reb': 889},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='compare lebron n harden assists',
        test_type=TestType.SQL,
        category='noisy_sql_abbreviation',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('LeBron James', 'James Harden') ORDER BY ps.ast DESC",
        ground_truth_data=[{'name': 'James Harden', 'ast': 687}, {'name': 'LeBron James', 'ast': 574}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='whats the avg fg% in da league lol',
        test_type=TestType.SQL,
        category='noisy_sql_slang',

        # SQL Expectations
        expected_sql='SELECT ROUND(AVG(fg_pct), 1) as avg_fg_pct FROM player_stats WHERE fg_pct IS NOT NULL',
        ground_truth_data={'avg_fg_pct': 44.6},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='top 3 reb guys??',
        test_type=TestType.SQL,
        category='noisy_sql_informal',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.reb DESC LIMIT 3',
        ground_truth_data=[{'name': 'Ivica Zubac', 'reb': 1008}, {'name': 'Domantas Sabonis', 'reb': 973}, {'name': 'Karl-Anthony Towns', 'reb': 922}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="'; DROP TABLE players; -- Who scored the most points?",
        test_type=TestType.SQL,
        category='adversarial_sql_injection',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1',
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'pts': 2485},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='SELECT * FROM players; Who has the most assists?',
        test_type=TestType.SQL,
        category='adversarial_raw_sql',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.ast DESC LIMIT 1',
        ground_truth_data={'name': 'Trae Young', 'ast': 882},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="../../etc/passwd What is Curry's three point percentage?",
        test_type=TestType.SQL,
        category='adversarial_path_traversal',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Stephen Curry%'",
        ground_truth_data={'name': 'Stephen Curry', 'three_pct': 39.7},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='What do Reddit users think about teams that have impressed in the playoffs?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What are the most popular opinions about the two best playoff teams?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What do fans debate about Reggie Miller's efficiency?",
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Which NBA teams didn't have home court advantage in finals according to discussions?",
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What do fans think about home court advantage in the playoffs?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='According to basketball discussions, what makes a player efficient in playoffs?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Do fans debate about historical playoff performances?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which playoff topics generate the most discussion on Reddit?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What do NBA fans consider surprising about playoff results?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What do fans think about NBA trades?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='What did u/MannerSuperb post about?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Tell me about the most discussed playoff efficiency topic.',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What's the most popular Reddit discussion about playoffs?",
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Show me highly upvoted comments about basketball.',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What do authoritative voices say about playoff basketball?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare opinions on efficiency from high-engagement vs low-engagement posts.',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What are the consensus views on playoff performance?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Find the most engaged discussion about NBA history.',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What do the top comments say about playoff success?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Show me verified or official perspectives on basketball.',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='What is a pick and roll?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Explain what PER means in basketball.',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What does zone defense mean?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Define true shooting percentage.',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is a triple-double?',
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Explain the difference between man-to-man and zone defense.',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What basketball terms are important for understanding efficiency?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What does 'first option' mean in basketball?",
        test_type=TestType.VECTOR,
        category='simple',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the weather forecast for Los Angeles tomorrow?',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How do I bake a chocolate cake?',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Tell me about the latest political election results.',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the stock price of Apple Inc.?',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Best strategy for winning in NBA 2K24 video game?',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="How to fix my computer's blue screen error?",
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What are the best restaurants in New York City?',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='?',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='asdfghjkl qwerty12345',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Give me a 10000 word essay on the history of the universe.',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Translate 'hello' to 50 different languages.",
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="<script>alert('XSS')</script> Who won the MVP?",
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question="'; DROP TABLE players; --",
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='../../../etc/passwd',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='{{7*7}} ${7*7} <%= 7*7 %>',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What do fans say about the Lakers?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='lakers_discussion',
    ),
    UnifiedTestCase(
        question='What are their biggest strengths?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='lakers_discussion',
    ),
    UnifiedTestCase(
        question='And their weaknesses?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='lakers_discussion',
    ),
    UnifiedTestCase(
        question='Tell me about playoff teams that surprised people.',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='playoff_surprises',
    ),
    UnifiedTestCase(
        question='Why were they surprising?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='playoff_surprises',
    ),
    UnifiedTestCase(
        question='Compare them to the top-seeded teams.',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='playoff_surprises',
    ),

    UnifiedTestCase(
        question='What makes a player efficient in the playoffs?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='efficiency_metrics',
    ),
    UnifiedTestCase(
        question='Who is the most efficient according to fans?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='efficiency_metrics',
    ),
    UnifiedTestCase(
        question='What do people debate about his efficiency?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='efficiency_metrics',
    ),
    UnifiedTestCase(
        question='Tell me about home court advantage in playoffs.',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='topic_switching',
    ),
    UnifiedTestCase(
        question='Going back to efficiency, who else is considered efficient?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='topic_switching',
    ),
    UnifiedTestCase(
        question='Returning to home court, which teams historically lacked it?',
        test_type=TestType.VECTOR,
        category='conversational',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='topic_switching',
    ),
    UnifiedTestCase(
        question='whos da best playa in playoffs acording 2 reddit',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='reggie milr effishency debat',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='lmao bro playoff teams are wild this year fr fr',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='imho home court dont matter much tbh',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='playoff playoff playoff teams teams impressive impressive',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='reddit nba thoughts???',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='yo what ppl saying bout top teams',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='nba',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='hello',
        test_type=TestType.VECTOR,
        category='noisy',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Analyze the evolution of playoff strategies based on fan discussions.',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What patterns emerge from Reddit debates about playoff performance?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How do fan perceptions of efficiency differ from statistical measures?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What controversies exist in evaluating playoff success?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Synthesize fan wisdom about what makes teams succeed in playoffs.',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='What basketball strategies do fans discuss for playoff success?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How has the NBA changed over the years according to fan discussions?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How many points did LeBron score and why do fans love him?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the overall sentiment about NBA playoffs on Reddit?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Can you give me a direct quote from the Reddit discussions about efficiency?',
        test_type=TestType.VECTOR,
        category='complex',

        # SQL Expectations
        expected_sql=None,
        ground_truth_data=None,

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who scored the most points this season and what makes them an effective scorer?',
        test_type=TestType.HYBRID,
        category='tier1_stat_plus_context',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1',
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'pts': 2485},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Compare LeBron James and Kevin Durant's scoring this season and explain their scoring styles.",
        test_type=TestType.HYBRID,
        category='tier1_comparison_plus_context',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.fg_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('LeBron James', 'Kevin Durant')",
        ground_truth_data=[{'name': 'LeBron James', 'pts': 1708}, {'name': 'Kevin Durant', 'pts': 1649}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What is Nikola Jokić's scoring average and why is he considered an elite offensive player?",
        test_type=TestType.HYBRID,
        category='tier1_stat_plus_explanation',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Jokić%'",
        ground_truth_data={'name': 'Nikola Jokić', 'pts': 2072, 'gp': 70},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who are the top 3 rebounders and what impact do they have on their teams?',
        test_type=TestType.HYBRID,
        category='tier1_leaders_plus_impact',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.reb DESC LIMIT 3',
        ground_truth_data=[{'name': 'Ivica Zubac', 'reb': 1008}, {'name': 'Domantas Sabonis', 'reb': 973}, {'name': 'Karl-Anthony Towns', 'reb': 922}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Compare Jokić and Embiid's stats and explain which one is more valuable based on their playing style.",
        test_type=TestType.HYBRID,
        category='tier2_comparison_advanced',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Nikola Jokić', 'Joel Embiid')",
        ground_truth_data=[{'name': 'Nikola Jokić', 'pts': 2072, 'reb': 889, 'ast': 714, 'pie': 20.6}, {'name': 'Joel Embiid', 'pts': 452, 'reb': 156, 'ast': 86, 'pie': 16.9}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Who are the most efficient scorers by true shooting percentage and what makes them efficient?',
        test_type=TestType.HYBRID,
        category='tier2_efficiency_analysis',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ts_pct, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 ORDER BY ps.ts_pct DESC LIMIT 5',
        ground_truth_data=[
            {"name": "Jarrett Allen", "ts_pct": 72.4, "pts": 1107},
            {"name": "Jaxson Hayes", "ts_pct": 72, "pts": 381},
            {"name": "Daniel Gafford", "ts_pct": 71.6, "pts": 701},
            {"name": "Adem Bona", "ts_pct": 71.4, "pts": 336},
            {"name": "Dwight Powell", "ts_pct": 71.3, "pts": 116}
        ],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Compare Giannis and Anthony Davis's rebounds and explain how their rebounding styles differ.",
        test_type=TestType.HYBRID,
        category='tier2_style_comparison',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.reb, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Giannis Antetokounmpo', 'Anthony Davis')",
        ground_truth_data=[{'name': 'Giannis Antetokounmpo', 'reb': 797}, {'name': 'Anthony Davis', 'reb': 592}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who has the best assist-to-turnover ratio among high-volume passers and why is this important?',
        test_type=TestType.HYBRID,
        category='tier2_efficiency_metric',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ast, ps.tov, ROUND(ps.ast*1.0/ps.tov, 2) as ratio FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ast >= 300 AND ps.tov > 0 ORDER BY (ps.ast*1.0/ps.tov) DESC LIMIT 5',
        ground_truth_data=[
            {"name": "Tyrese Haliburton", "ast": 672, "tov": 117, "ratio": 5.74},
            {"name": "Tyus Jones", "ast": 429, "tov": 89, "ratio": 4.82},
            {"name": "Chris Paul", "ast": 607, "tov": 131, "ratio": 4.63},
            {"name": "Mike Conley", "ast": 320, "tov": 78, "ratio": 4.1},
            {"name": "Fred VanVleet", "ast": 336, "tov": 90, "ratio": 3.73}
        ],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Find players averaging triple-double stats and explain what makes this achievement so rare and valuable.',
        test_type=TestType.HYBRID,
        category='tier3_rare_achievement',

        # SQL Expectations
        expected_sql='SELECT p.name, ROUND(ps.pts*1.0/ps.gp,1) as ppg, ROUND(ps.reb*1.0/ps.gp,1) as rpg, ROUND(ps.ast*1.0/ps.gp,1) as apg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 0 AND ps.pts*1.0/ps.gp >= 10 AND ps.reb*1.0/ps.gp >= 10 AND ps.ast*1.0/ps.gp >= 10',
        ground_truth_data=[{'name': 'Nikola Jokić', 'ppg': 29.6, 'rpg': 12.7, 'apg': 10.2}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which players have high scoring but low efficiency, and why might teams still rely on them?',
        test_type=TestType.HYBRID,
        category='tier3_strategic_tradeoff',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.fg_pct, ps.ts_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 1500 AND ps.fg_pct < 45 ORDER BY ps.pts DESC',
        ground_truth_data=[
            {"name": "Anthony Edwards", "pts": 2180, "fg_pct": 44.7, "ts_pct": 59.5},
            {"name": "Trae Young", "pts": 1839, "fg_pct": 41.1, "ts_pct": 56.7},
            {"name": "James Harden", "pts": 1801, "fg_pct": 41, "ts_pct": 58.2},
            {"name": "Jalen Green", "pts": 1722, "fg_pct": 42.3, "ts_pct": 54.4},
            {"name": "Stephen Curry", "pts": 1715, "fg_pct": 44.8, "ts_pct": 61.8},
            {"name": "Donovan Mitchell", "pts": 1704, "fg_pct": 44.3, "ts_pct": 57.5}
        ],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare the top defensive players by blocks and steals and explain different defensive styles.',
        test_type=TestType.HYBRID,
        category='tier3_defensive_styles',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.stl, ps.blk, (ps.stl + ps.blk) as def_actions FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY (ps.stl + ps.blk) DESC LIMIT 5',
        ground_truth_data=[{'name': 'Dyson Daniels', 'stl': 228, 'blk': 53, 'def_actions': 281}, {'name': 'Victor Wembanyama', 'stl': 51, 'blk': 175, 'def_actions': 226}, {'name': 'Shai Gilgeous-Alexander', 'stl': 129, 'blk': 76, 'def_actions': 205}, {'name': 'Myles Turner', 'stl': 58, 'blk': 144, 'def_actions': 202}, {'name': 'Jaren Jackson Jr,', 'stl': 89, 'blk': 111, 'def_actions': 200}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Analyze players with 1500+ points and 400+ assists - what does this dual threat mean strategically?',
        test_type=TestType.HYBRID,
        category='tier3_dual_threat_strategy',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts >= 1500 AND ps.ast >= 300 ORDER BY ps.pts DESC LIMIT 5',
        ground_truth_data=[{'name': 'Shai Gilgeous-Alexander', 'pts': 2485, 'ast': 486}, {'name': 'Anthony Edwards', 'pts': 2180, 'ast': 356}, {'name': 'Nikola Jokić', 'pts': 2072, 'ast': 714}, {'name': 'Giannis Antetokounmpo', 'pts': 2037, 'ast': 436}, {'name': 'Jayson Tatum', 'pts': 1930, 'ast': 432}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What's the relationship between three-point shooting volume and efficiency, and how has this changed the modern NBA?",
        test_type=TestType.HYBRID,
        category='tier4_league_trend_analysis',

        # SQL Expectations
        expected_sql='SELECT AVG(three_pct) as avg_3p, COUNT(*) as player_count FROM player_stats WHERE three_pct IS NOT NULL',
        ground_truth_data={'avg_3p': 29.9},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare advanced efficiency metrics (PIE, TS%) for MVP candidates and explain what these metrics reveal about player impact.',
        test_type=TestType.HYBRID,
        category='tier4_advanced_metrics_interpretation',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pie, ps.ts_pct, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 1800 ORDER BY ps.pie DESC LIMIT 5',
        ground_truth_data=[
            {"name": "Giannis Antetokounmpo", "pie": 21, "ts_pct": 62.5, "pts": 2037},
            {"name": "Nikola Jokić", "pie": 20.6, "ts_pct": 66.3, "pts": 2072},
            {"name": "Shai Gilgeous-Alexander", "pie": 19.9, "ts_pct": 63.7, "pts": 2485},
            {"name": "Jayson Tatum", "pie": 15.8, "ts_pct": 58.2, "pts": 1930},
            {"name": "Cade Cunningham", "pie": 15.2, "ts_pct": 56.5, "pts": 1827}
        ],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="How do young players (high stats) compare to established stars, and what does this suggest about the league's future?",
        test_type=TestType.HYBRID,
        category='tier4_generational_shift',

        # SQL Expectations
        expected_sql='SELECT p.name, p.age, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.age IS NOT NULL ORDER BY ps.pts DESC LIMIT 10',
        ground_truth_data=[
            {"name": "Shai Gilgeous-Alexander", "age": 26, "pts": 2485, "pie": 19.9},
            {"name": "Anthony Edwards", "age": 23, "pts": 2180, "pie": 14},
            {"name": "Nikola Jokić", "age": 30, "pts": 2072, "pie": 20.6},
            {"name": "Giannis Antetokounmpo", "age": 30, "pts": 2037, "pie": 21},
            {"name": "Jayson Tatum", "age": 27, "pts": 1930, "pie": 15.8},
            {"name": "Devin Booker", "age": 28, "pts": 1920, "pie": 12.2},
            {"name": "Tyler Herro", "age": 25, "pts": 1840, "pie": 13.9},
            {"name": "Trae Young", "age": 26, "pts": 1839, "pie": 12.9},
            {"name": "Cade Cunningham", "age": 23, "pts": 1827, "pie": 15.2},
            {"name": "James Harden", "age": 35, "pts": 1801, "pie": 14.5}
        ],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Analyze the correlation between assists and team success - which high-assist players drive winning?',
        test_type=TestType.HYBRID,
        category='tier4_correlation_analysis',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ast, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ast > 500 ORDER BY ps.ast DESC LIMIT 5',
        ground_truth_data=[{'name': 'Trae Young', 'ast': 882, 'pie': 12.9}, {'name': 'Nikola Jokić', 'ast': 714, 'pie': 20.6}, {'name': 'James Harden', 'ast': 687, 'pie': 14.5}, {'name': 'Tyrese Haliburton', 'ast': 672, 'pie': 14.3}, {'name': 'Cade Cunningham', 'ast': 637, 'pie': 15.2}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the average scoring for the Warriors and how is their team culture described by fans?',
        test_type=TestType.HYBRID,
        category='tier2_team_aggregation',

        # SQL Expectations
        expected_sql="SELECT ROUND(AVG(ps.pts), 1) as avg_pts, COUNT(*) as player_count FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'GSW'",
        ground_truth_data={'avg_pts': 487.5, 'player_count': 17},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Actually, compare Giannis to Jokić instead and explain who fans think is better',
        test_type=TestType.HYBRID,
        category='tier2_correction_comparison',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Giannis Antetokounmpo', 'Nikola Jokić')",
        ground_truth_data=[{'name': 'Giannis Antetokounmpo', 'pts': 2037, 'reb': 797, 'ast': 436, 'pie': 21.0}, {'name': 'Nikola Jokić', 'pts': 2072, 'reb': 889, 'ast': 714, 'pie': 20.6}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who is LeBron?',
        test_type=TestType.HYBRID,
        category='hybrid_player_profile',

        # SQL Expectations
        expected_sql="SELECT p.name, t.name as team, p.age, ps.gp, ps.pts, ps.reb, ps.ast, ps.stl, ps.blk, ps.fg_pct, ps.three_pct, ps.ft_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id JOIN teams t ON p.team_abbr = t.abbreviation WHERE p.name LIKE '%LeBron%'",
        ground_truth_data={'name': 'LeBron James', 'team': 'Los Angeles Lakers', 'age': 40, 'gp': 70, 'pts': 1708, 'reb': 546, 'ast': 574, 'stl': 70, 'blk': 42, 'fg_pct': 51.3, 'three_pct': 37.6, 'ft_pct': 78.2},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Tell me about Anthony Edwards' season stats and what makes him such an exciting player to watch",
        test_type=TestType.HYBRID,
        category='hybrid_player_profile',

        # SQL Expectations
        expected_sql="SELECT p.name, p.age, ps.pts, ps.reb, ps.ast, ps.gp, ROUND(ps.pts*1.0/ps.gp, 1) as ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Anthony Edwards%'",
        ground_truth_data={'name': 'Anthony Edwards', 'age': 23, 'pts': 2180, 'reb': 450, 'ast': 356, 'gp': 79, 'ppg': 27.6},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What are Victor Wembanyama's stats and why are fans so excited about his potential?",
        test_type=TestType.HYBRID,
        category='hybrid_player_profile',

        # SQL Expectations
        expected_sql="SELECT p.name, p.age, ps.pts, ps.reb, ps.blk, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Wembanyama%'",
        ground_truth_data={'name': 'Victor Wembanyama', 'age': 21, 'pts': 1118, 'reb': 506, 'blk': 175, 'gp': 46},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Show me Trae Young's stats — is he underrated or overrated according to fans?",
        test_type=TestType.HYBRID,
        category='hybrid_player_profile',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.ast, ps.fg_pct, ps.tov FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Trae Young%'",
        ground_truth_data={'name': 'Trae Young', 'pts': 1839, 'ast': 882, 'fg_pct': 41.1, 'tov': 357},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What are Cade Cunningham's numbers this season and what do fans think about his development?",
        test_type=TestType.HYBRID,
        category='hybrid_player_profile',

        # SQL Expectations
        expected_sql="SELECT p.name, p.age, ps.pts, ps.reb, ps.ast, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Cade Cunningham%'",
        ground_truth_data={'name': 'Cade Cunningham', 'age': 23, 'pts': 1827, 'reb': 427, 'ast': 637, 'gp': 70},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Compare the Celtics and Lakers stats and how fans view each team's championship hopes",
        test_type=TestType.HYBRID,
        category='hybrid_team_comparison',

        # SQL Expectations
        expected_sql="SELECT p.team_abbr, SUM(ps.pts) as total_pts, SUM(ps.reb) as total_reb, SUM(ps.ast) as total_ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr IN ('BOS', 'LAL') GROUP BY p.team_abbr ORDER BY total_pts DESC",
        ground_truth_data=[{'team_abbr': 'BOS', 'total_pts': 9551, 'total_reb': 3723, 'total_ast': 2147}, {'team_abbr': 'LAL', 'total_pts': 8691, 'total_reb': 3321, 'total_ast': 2135}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='How do the Thunder and Nuggets compare statistically, and what do fans say about their playoff chances?',
        test_type=TestType.HYBRID,
        category='hybrid_team_comparison',

        # SQL Expectations
        expected_sql="SELECT p.team_abbr, SUM(ps.pts) as total_pts, ROUND(AVG(ps.pts), 1) as avg_pts, SUM(ps.ast) as total_ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr IN ('OKC', 'DEN') GROUP BY p.team_abbr ORDER BY total_pts DESC",
        ground_truth_data=[{'team_abbr': 'DEN', 'total_pts': 9899, 'avg_pts': 582.3, 'total_ast': 2538}, {'team_abbr': 'OKC', 'total_pts': 9880, 'avg_pts': 548.9, 'total_ast': 2195}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Which team plays the best defense by stats, and how do fans describe their defensive identity?',
        test_type=TestType.HYBRID,
        category='hybrid_team_defense',

        # SQL Expectations
        expected_sql='SELECT p.team_abbr, SUM(ps.stl + ps.blk) as def_actions, SUM(ps.stl) as total_stl, SUM(ps.blk) as total_blk FROM players p JOIN player_stats ps ON p.id = ps.player_id GROUP BY p.team_abbr ORDER BY def_actions DESC LIMIT 1',
        ground_truth_data={'team_abbr': 'OKC', 'def_actions': 1298, 'total_stl': 840, 'total_blk': 458},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Show me the Pacers' team stats — why have fans found them impressive this season?",
        test_type=TestType.HYBRID,
        category='hybrid_team_profile',

        # SQL Expectations
        expected_sql="SELECT p.team_abbr, SUM(ps.pts) as total_pts, ROUND(AVG(ps.pts), 1) as avg_pts, SUM(ps.ast) as total_ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'IND' GROUP BY p.team_abbr",
        ground_truth_data={'team_abbr': 'IND', 'total_pts': 9630, 'avg_pts': 481.5, 'total_ast': 2395},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which young players under 25 are putting up the best numbers, and what do fans expect from the next generation?',
        test_type=TestType.HYBRID,
        category='hybrid_young_talent',

        # SQL Expectations
        expected_sql='SELECT p.name, p.age, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.age < 25 AND ps.pts > 1000 ORDER BY ps.pts DESC LIMIT 5',
        ground_truth_data=[{'name': 'Anthony Edwards', 'age': 23, 'pts': 2180}, {'name': 'Cade Cunningham', 'age': 23, 'pts': 1827}, {'name': 'Jalen Green', 'age': 23, 'pts': 1722}, {'name': 'Jalen Williams', 'age': 24, 'pts': 1490}, {'name': 'Alperen Sengun', 'age': 22, 'pts': 1452}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Tell me about the youngest stars under 22 and how fans rate their potential',
        test_type=TestType.HYBRID,
        category='hybrid_young_talent',

        # SQL Expectations
        expected_sql='SELECT p.name, p.age, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.age <= 22 AND ps.pts > 500 ORDER BY ps.pts DESC LIMIT 5',
        ground_truth_data=[{'name': 'Alperen Sengun', 'age': 22, 'pts': 1452}, {'name': 'Shaedon Sharpe', 'age': 22, 'pts': 1332}, {'name': 'Paolo Banchero', 'age': 22, 'pts': 1191}, {'name': 'Stephon Castle', 'age': 20, 'pts': 1191}, {'name': 'Bennedict Mathurin', 'age': 22, 'pts': 1159}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="How do veteran players over 35 compare to young talent, and what do fans debate about the NBA's generational shift?",
        test_type=TestType.HYBRID,
        category='hybrid_generational',

        # SQL Expectations
        expected_sql='SELECT p.name, p.age, ps.pts, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.age >= 35 ORDER BY ps.pts DESC LIMIT 5',
        ground_truth_data=[{'name': 'James Harden', 'age': 35, 'pts': 1801, 'gp': 79}, {'name': 'Stephen Curry', 'age': 37, 'pts': 1715, 'gp': 70}, {'name': 'DeMar DeRozan', 'age': 35, 'pts': 1709, 'gp': 77}, {'name': 'LeBron James', 'age': 40, 'pts': 1708, 'gp': 70}, {'name': 'Kevin Durant', 'age': 36, 'pts': 1649, 'gp': 62}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="How do this season's 2000+ point scorers compare to the playoff efficiency legends that fans debate on Reddit?",
        test_type=TestType.HYBRID,
        category='hybrid_historical',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.gp, ROUND(ps.pts*1.0/ps.gp, 1) as ppg FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts >= 2000 ORDER BY ps.pts DESC',
        ground_truth_data=[{'name': 'Shai Gilgeous-Alexander', 'pts': 2485, 'gp': 76, 'ppg': 32.7}, {'name': 'Anthony Edwards', 'pts': 2180, 'gp': 79, 'ppg': 27.6}, {'name': 'Nikola Jokić', 'pts': 2072, 'gp': 70, 'ppg': 29.6}, {'name': 'Giannis Antetokounmpo', 'pts': 2037, 'gp': 67, 'ppg': 30.4}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Fans debate about Reggie Miller's playoff efficiency — how do current top shooters' true shooting compare?",
        test_type=TestType.HYBRID,
        category='hybrid_historical',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ts_pct, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 AND ps.pts > 1000 ORDER BY ps.ts_pct DESC LIMIT 5',
        ground_truth_data=[{'name': 'Jarrett Allen', 'ts_pct': 72.4}, {'name': 'Christian Braun', 'ts_pct': 66.5}, {'name': 'Nikola Jokić', 'ts_pct': 66.3}, {'name': 'Harrison Barnes', 'ts_pct': 65.6}, {'name': 'Domantas Sabonis', 'ts_pct': 65.5}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which current players match the historical playoff dominance that fans discuss on Reddit?',
        test_type=TestType.HYBRID,
        category='hybrid_historical',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 ORDER BY ps.pie DESC LIMIT 5',
        ground_truth_data=[
            {"name": "Giannis Antetokounmpo", "pts": 2037, "pie": 21},
            {"name": "Nikola Jokić", "pts": 2072, "pie": 20.6},
            {"name": "Shai Gilgeous-Alexander", "pts": 2485, "pie": 19.9},
            {"name": "Anthony Davis", "pts": 1260, "pie": 17.9},
            {"name": "LeBron James", "pts": 1708, "pie": 16.9}
        ],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which high-volume scorers have poor shooting efficiency, and are they still considered valuable by fans?',
        test_type=TestType.HYBRID,
        category='hybrid_contrast',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.fg_pct, ps.ts_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 1500 AND ps.fg_pct < 45 ORDER BY ps.pts DESC LIMIT 5',
        ground_truth_data=[{'name': 'Anthony Edwards', 'pts': 2180, 'fg_pct': 44.7}, {'name': 'Trae Young', 'pts': 1839, 'fg_pct': 41.1}, {'name': 'James Harden', 'pts': 1801, 'fg_pct': 41.0}, {'name': 'Jalen Green', 'pts': 1722, 'fg_pct': 42.3}, {'name': 'Stephen Curry', 'pts': 1715, 'fg_pct': 44.8}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who leads in assists but also in turnovers — do fans think high usage is worth the mistakes?',
        test_type=TestType.HYBRID,
        category='hybrid_contrast',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.ast, ps.tov FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Trae Young%'",
        ground_truth_data={'name': 'Trae Young', 'ast': 882, 'tov': 357},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Are there players with modest scoring but exceptional all-around impact, and what does this reveal about value?',
        test_type=TestType.HYBRID,
        category='hybrid_contrast',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 AND ps.pie > 15 ORDER BY ps.pie DESC LIMIT 5',
        ground_truth_data=[
            {"name": "Giannis Antetokounmpo", "pts": 2037, "pie": 21},
            {"name": "Nikola Jokić", "pts": 2072, "pie": 20.6},
            {"name": "Shai Gilgeous-Alexander", "pts": 2485, "pie": 19.9},
            {"name": "Anthony Davis", "pts": 1260, "pie": 17.9},
            {"name": "LeBron James", "pts": 1708, "pie": 16.9}
        ],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What are Shai Gilgeous-Alexander's full stats this season?",
        test_type=TestType.HYBRID,
        category='hybrid_conversational_mvp',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast, ps.fg_pct, ps.gp FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Shai%'",
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'pts': 2485, 'reb': 380, 'ast': 486, 'fg_pct': 51.9, 'gp': 76},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='mvp_sga_discussion',
    ),
    UnifiedTestCase(
        question='Why do fans on Reddit consider him an MVP favorite?',
        test_type=TestType.HYBRID,
        category='hybrid_conversational_mvp',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pie, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Shai%'",
        ground_truth_data={"name": "Shai Gilgeous-Alexander", "pie": 19.9, "pts": 2485},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='mvp_sga_discussion',
    ),
    UnifiedTestCase(
        question='How does his efficiency compare to the historical playoff scorers that fans debate about?',
        test_type=TestType.HYBRID,
        category='hybrid_conversational_mvp',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.ts_pct, ps.efg_pct, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Shai%'",
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'ts_pct': 63.7, 'efg_pct': 56.9, 'pie': 19.9},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='mvp_sga_discussion',
    ),
    UnifiedTestCase(
        question="Show me the Celtics' team statistics this season",
        test_type=TestType.HYBRID,
        category='hybrid_conversational_team',

        # SQL Expectations
        expected_sql="SELECT p.team_abbr, SUM(ps.pts) as total_pts, ROUND(AVG(ps.pts), 1) as avg_pts, SUM(ps.reb) as total_reb, SUM(ps.ast) as total_ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'BOS' GROUP BY p.team_abbr",
        ground_truth_data={'team_abbr': 'BOS', 'total_pts': 9551, 'avg_pts': 561.8, 'total_reb': 3723, 'total_ast': 2147},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='team_celtics_deepdive',
    ),
    UnifiedTestCase(
        question='What do fans think about their chances of repeating as champions?',
        test_type=TestType.HYBRID,
        category='hybrid_conversational_team',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'BOS' ORDER BY ps.pts DESC LIMIT 3",
        ground_truth_data=[
            {"name": "Jayson Tatum", "pts": 1930},
            {"name": "Jaylen Brown", "pts": 1399},
            {"name": "Derrick White", "pts": 1246}
        ],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='team_celtics_deepdive',
    ),
    UnifiedTestCase(
        question='Compare their stats to the Nuggets — which team is statistically better?',
        test_type=TestType.HYBRID,
        category='hybrid_conversational_team',

        # SQL Expectations
        expected_sql="SELECT p.team_abbr, SUM(ps.pts) as total_pts, ROUND(AVG(ps.pts), 1) as avg_pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr IN ('BOS', 'DEN') GROUP BY p.team_abbr ORDER BY total_pts DESC",
        ground_truth_data=[{'team_abbr': 'DEN', 'total_pts': 9899, 'avg_pts': 582.3}, {'team_abbr': 'BOS', 'total_pts': 9551, 'avg_pts': 561.8}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread='team_celtics_deepdive',
    ),
    UnifiedTestCase(
        question='yo whos got da best stats AND what do ppl think about them on reddit',
        test_type=TestType.HYBRID,
        category='hybrid_noisy',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 1',
        ground_truth_data={'name': 'Shai Gilgeous-Alexander', 'pts': 2485},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='lebron stats + fan opinions plzzz',
        test_type=TestType.HYBRID,
        category='hybrid_noisy',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.reb, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%LeBron%'",
        ground_truth_data={'name': 'LeBron James', 'pts': 1708, 'reb': 546, 'ast': 574},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='compare curry n jokic stats nd tell me who fans like more',
        test_type=TestType.HYBRID,
        category='hybrid_noisy',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts, ps.ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name IN ('Stephen Curry', 'Nikola Jokić') ORDER BY ps.pts DESC",
        ground_truth_data=[{'name': 'Nikola Jokić', 'pts': 2072, 'ast': 714}, {'name': 'Stephen Curry', 'pts': 1715, 'ast': 420}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Who leads the league in blocks and what makes them elite defenders according to fans?',
        test_type=TestType.HYBRID,
        category='hybrid_defensive',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.blk, ps.pts, ps.reb FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.blk DESC LIMIT 1',
        ground_truth_data={'name': 'Victor Wembanyama', 'blk': 175, 'pts': 1118, 'reb': 506},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which players have the highest PIE and what does this metric reveal about their value according to fan discussions?',
        test_type=TestType.HYBRID,
        category='hybrid_advanced_metrics',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pie, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 ORDER BY ps.pie DESC LIMIT 5',
        ground_truth_data=[{'name': 'Giannis Antetokounmpo', 'pie': 21.0}, {'name': 'Nikola Jokić', 'pie': 20.6}, {'name': 'Shai Gilgeous-Alexander', 'pie': 19.9}, {'name': 'Anthony Davis', 'pie': 17.9}, {'name': 'LeBron James', 'pie': 16.9}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare the top 3 assist leaders and explain what fans think about playmaking in modern basketball',
        test_type=TestType.HYBRID,
        category='hybrid_playmaking',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ast, ps.gp, ROUND(ps.ast*1.0/ps.gp, 1) as apg FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.ast DESC LIMIT 3',
        ground_truth_data=[{'name': 'Trae Young', 'ast': 882, 'gp': 76, 'apg': 11.6}, {'name': 'Nikola Jokić', 'ast': 714, 'gp': 70, 'apg': 10.2}, {'name': 'James Harden', 'ast': 687, 'gp': 79, 'apg': 8.7}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="What are the Thunder's stats this season and how do fans describe their team identity?",
        test_type=TestType.HYBRID,
        category='hybrid_team_culture',

        # SQL Expectations
        expected_sql="SELECT p.team_abbr, SUM(ps.pts) as total_pts, ROUND(AVG(ps.pts), 1) as avg_pts, SUM(ps.reb) as total_reb, SUM(ps.ast) as total_ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'OKC' GROUP BY p.team_abbr",
        ground_truth_data={'team_abbr': 'OKC', 'total_pts': 9880, 'avg_pts': 548.9, 'total_reb': 3660, 'total_ast': 2195},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="Show me the Timberwolves' numbers and what fans call their 'young and hungry' identity",
        test_type=TestType.HYBRID,
        category='hybrid_team_culture',

        # SQL Expectations
        expected_sql="SELECT p.team_abbr, SUM(ps.pts) as total_pts, ROUND(AVG(ps.pts), 1) as avg_pts, SUM(ps.reb) as total_reb, SUM(ps.ast) as total_ast FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'MIN' GROUP BY p.team_abbr",
        ground_truth_data={'team_abbr': 'MIN', 'total_pts': 9523, 'avg_pts': 476.1, 'total_reb': 3656, 'total_ast': 2175},

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who are the top 3-point shooters by volume and how has the three-point revolution changed the game according to fans?',
        test_type=TestType.HYBRID,
        category='hybrid_shooting_evolution',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.three_pa, ps.three_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.three_pa DESC LIMIT 3',
        ground_truth_data=[{'name': 'Anthony Edwards', 'three_pa': 814, 'three_pct': 39.5}, {'name': 'Stephen Curry', 'three_pa': 784, 'three_pct': 39.7}, {'name': 'Malik Beasley', 'three_pa': 763, 'three_pct': 41.6}],

        # Vector Expectations
        ground_truth_vector=None,

        # Optional: Conversation context
        conversation_thread=None,
    ),
]

# ============================================================================
# STATISTICS
# ============================================================================

def get_statistics():
    """Get test case statistics."""
    return {
        "total": 206,
        "sql": 80,
        "vector": 75,
        "hybrid": 51,
    }

if __name__ == "__main__":
    stats = get_statistics()
    logger.info(f"Total test cases: {stats['total']}")
    logger.info(f"  SQL: {stats['sql']}")
    logger.info(f"  Vector: {stats['vector']}")
    logger.info(f"  Hybrid: {stats['hybrid']}")
