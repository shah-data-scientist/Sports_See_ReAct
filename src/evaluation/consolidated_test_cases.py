"""
FILE: consolidated_test_cases.py
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
- Removed redundant fields: query_type, min_similarity_score, tags, difficulty, description
- Updated validation: ground_truth_answer now REQUIRED for all types
- Unified validation logic (no type-specific validation)
"""

from src.evaluation.unified_model import UnifiedTestCase, TestType

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Shai Gilgeous-Alexander scored the most points with 2485 PTS.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 3 rebounders: Ivica Zubac (1008), Domantas Sabonis (973), Karl-Anthony Towns (922).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 steals: Dyson Daniels (228), Shai Gilgeous-Alexander (129), Nikola Jokić (126), Kris Dunn (126), Cason Wallace (122).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Sam Hauser has the best free throw percentage at 100%.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Kai Jones has the highest true shooting percentage at 80.4%.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='LeBron James averages 24.4 points per game.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Stephen Curry's 3-point percentage is 39.7%.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Nikola Jokić has 889 rebounds.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Chris Paul recorded 607 assists.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='There are 20 players on the Lakers roster.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Warriors roster: Brandin Podziemski, Braxton Key, Buddy Hield, Draymond Green, Gary Payton II, Gui Santos, Jackson Rowe, Jimmy Butler III, Jonathan Kuminga, Kevon Looney, Kevin Knox II, Moses Moody, Pat Spencer, Quinten Post, Stephen Curry, Trayce Jackson-Davis, Yuri Collins (17 players).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Jarrett Allen has the most wins with 64.',

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='What is the average player age in the NBA?',
        test_type=TestType.SQL,
        category='aggregation_sql_league',

        # SQL Expectations
        expected_sql='SELECT AVG(age) as avg_age FROM players WHERE age IS NOT NULL',
        ground_truth_data={'avg_age': 26.15},

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The average player age in the NBA is 26.15 years.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Nikola Jokić: 2072 PTS, 889 REB, 714 AST. Joel Embiid: 452 PTS, 156 REB, 86 AST.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Stephen Curry shoots better (39.7%) than Damian Lillard (37.6%).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Nikola Jokić is more efficient: FG% 57.6, EFG% 62.7 vs Joel Embiid FG% 44.4, EFG% 48.1.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Jayson Tatum: 1930 PTS, 45.2% FG, 53.7% EFG, 58.2% TS. Kevin Durant: 1649 PTS, 52.7% FG, 59.8% EFG, 64.2% TS.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='James Harden has more assists (687) than Chris Paul (607).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 2 steals: Dyson Daniels (228), Shai Gilgeous-Alexander (129).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Victor Wembanyama (175 BLK) leads, followed by Brook Lopez (152 BLK).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The average 3-point percentage across all players is 29.9%.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The average field goal percentage is 44.6%.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The average PIE is 8.9.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The average rebounds per game is 3.60 RPG.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='84 players scored over 1000 points this season.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='118 players (with 20+ games played) have a true shooting percentage over 60%.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='10 players have more than 500 assists.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='282 players played more than 50 games.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The highest PIE is 40.0.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Victor Wembanyama has the maximum blocks with 175.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The average field goal percentage for the Lakers is 44.6%.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 above-avg PPG: Shai Gilgeous-Alexander (32.7), Giannis Antetokounmpo (30.4), Nikola Jokić (29.6), Luka Dončić (28.2), Anthony Edwards (27.6).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 4 dual-threat players: Shai Gilgeous-Alexander (2485 PTS, 486 AST), Anthony Edwards (2180 PTS, 356 AST), Nikola Jokić (2072 PTS, 714 AST), Giannis Antetokounmpo (2037 PTS, 436 AST).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 with FG>50% AND 3P>35% (50+ games): Dwight Powell (68.9 FG%, 40.0 3P%), Drew Eubanks (59.3 FG%, 50.0 3P%), Domantas Sabonis (59.0 FG%, 41.7 3P%), Christian Braun (58.0 FG%, 39.7 3P%), Nikola Jokić (57.6 FG%, 41.7 3P%).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Rare players averaging 10+ PPG, RPG, and APG (triple-double averages).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 defenders: Dyson Daniels (281), Victor Wembanyama (226), Shai Gilgeous-Alexander (205), Myles Turner (202), Jaren Jackson Jr. (200).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Best AST/TO (300+ AST): Tyrese Haliburton (5.74), Tyus Jones (4.82), Chris Paul (4.63), Mike Conley (4.10), Fred VanVleet (3.73).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='25.9% of players (118 out of 456 with 20+ games) have a true shooting percentage above 60%.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 most efficient (EFG%, 50+ GP): Jaxson Hayes (72.2), Jarrett Allen (70.6), Dwight Powell (70.5), Adem Bona (70.3), Daniel Gafford (70.2).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 3 PPG (70+ GP): Shai Gilgeous-Alexander (32.7), Nikola Jokić (29.6), Anthony Edwards (27.6).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 versatile (1000+ PTS, 400+ REB, 200+ AST): Nikola Jokić (2072/889/714), Giannis Antetokounmpo (2037/797/436), Jayson Tatum (1930/626/432), Anthony Edwards (2180/450/356), James Harden (1801/458/687).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 teams by avg points per player: DEN (582.3), SAS (566.6), CLE (565.6), BOS (561.8), OKC (548.9).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Celtics average 561.8 points per player (17 players) vs Lakers 434.6 (20 players).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Teams with 3+ high scorers (1000+ pts): SAS (5), NYK (5), CLE (5), SAC (4), IND (4).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 scorers aged 25-30: Shai Gilgeous-Alexander (26, 2485), Nikola Jokić (30, 2072), Giannis Antetokounmpo (30, 2037), Jayson Tatum (27, 1930), Devin Booker (28, 1920).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Shai Gilgeous-Alexander is the top scorer with 2485 points.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Ivica Zubac is the top rebounder with 1008 rebounds.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='LeBron James: 1708 PTS, 546 REB, 574 AST.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 assist leaders: Trae Young (882), Nikola Jokić (714), James Harden (687), Tyrese Haliburton (672), Cade Cunningham (637).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Shai Gilgeous-Alexander has 486 assists (follow-up).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Ivica Zubac played 80 games (contextual follow-up).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='LeBron James: 1708 PTS, 546 REB, 574 AST. Stephen Curry: 1715 PTS, 308 REB, 420 AST.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Trae Young plays for the Hawks with 882 assists.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top pts leaders: Shai Gilgeous-Alexander (2485), Anthony Edwards (2180), Nikola Jokić (2072), Giannis Antetokounmpo (2037), Jayson Tatum (1930).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Giannis Antetokounmpo leads in PIE (21.0) with 2037 points, making him a top MVP candidate.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 3P shooters (>38%, 50+ GP): Drew Eubanks (50.0%), Seth Curry (45.6%), Zach LaVine (44.6%), Ty Jerome (43.9%), Taurean Prince (43.9%).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Lakers 3P shooters: Rui Hachimura (41.3%), Dorian Finney-Smith (41.1%), Jordan Goodwin (38.2%), Austin Reaves (37.7%), LeBron James (37.6%).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Lakers 3P by attempts: Austin Reaves (37.7%, 533 3PA), Luka Dončić (36.8%, 480 3PA), LeBron James (37.6%, 399 3PA), Dalton Knecht (37.6%, 343 3PA), Dorian Finney-Smith (41.1%, 315 3PA).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Warriors top 3: Stephen Curry (1715 PTS, 308 REB, 420 AST), Jimmy Butler III (963 PTS, 297 REB, 297 AST), Buddy Hield (910 PTS, 262 REB, 131 AST).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Celtics top 3: Jayson Tatum (1930 PTS, 626 REB, 432 AST), Jaylen Brown (1399 PTS, 365 REB, 284 AST), Derrick White (1246 PTS, 342 REB, 365 AST).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Jayson Tatum is the Celtics' top scorer with 1930 points.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Dyson Daniels leads in steals with 228.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Victor Wembanyama leads in blocks with 175.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Trae Young leads in turnovers with 357.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Jayson Tatum: 1930 PTS in 72 GP (26.8 PPG).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Jayson Tatum: 1930 PTS (26.8 PPG). LeBron James: 1708 PTS (24.4 PPG).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Jayson Tatum has more rebounds (626) than LeBron James (546).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The Detroit Pistons (DET) have the highest total points with 10292.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Pistons top scorers: Cade Cunningham (1827), Malik Beasley (1337), Tobias Harris (1000).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The average age of the Pistons players is 25.3 years.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Shai Gilgeous-Alexander has the most points with 2485.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Stephen Curry's 3-point percentage is 39.7%.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='84 players scored over 1000 points.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Nikola Jokić has 889 total rebounds.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='James Harden has 687 assists vs LeBron James with 574.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='The average field goal percentage in the league is 44.6%.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 3 rebounders: Ivica Zubac (1008), Domantas Sabonis (973), Karl-Anthony Towns (922).',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Shai Gilgeous-Alexander scored the most with 2485 points.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Trae Young leads in assists with 882.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Stephen Curry's 3-point percentage is 39.7%.",

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
        ground_truth="Should retrieve Reddit 1.pdf: 'Who are teams in the playoffs that have impressed you?' by u/MannerSuperb (31 upvotes, 236 comments). Expected teams mentioned: Magic (Paolo Banchero, Franz Wagner), ...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 2.pdf: 'How is it that the two best teams in the playoffs based on stats, having a chance of playing against each other in the Finals, is considered to be a snoozefest?' by u...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 3.pdf: 'Reggie Miller is the most efficient first option in NBA playoffs' by u/hqppp (1300 post upvotes, up to 11515 comment upvotes - HIGHEST engagement). Expected discussio...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 4.pdf: 'Which NBA team did not have home court advantage until the NBA Finals?' by u/DonT012 (272 upvotes, 51 comments). Top answer (240 upvotes): 'Six teams have made the Fi...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve Reddit 4.pdf about home court advantage. Comments discuss: play-in tournament implications, how lower-seeded teams (below 4 seed) never had home court in Finals, importance of seedi...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 3.pdf discussion about playoff efficiency. Content includes TS% metric (True Shooting %), comparison table of 20 players' playoff efficiency, discussion of what qualifies as ...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve Reddit 3.pdf (historical efficiency comparison of 20 players across playoff history) and Reddit 4.pdf (historical home court examples: 2020 Lakers, 1995 Rockets). Both posts contain...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve chunks prioritized by post engagement boosting (0-1%): (1) Reddit 3 (1300 upvotes) - efficiency, (2) Reddit 2 (457 upvotes) - two best teams debate, (3) Reddit 4 (272 upvotes) - hom...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 1.pdf (teams that impressed: Magic, Wolves, Pacers exceeding expectations) and potentially Reddit 2.pdf (debate about whether 'two best teams' being a 'snoozefest' is surpris...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve Reddit discussions that mention trades or player movement. Reddit 1.pdf may contain comments about team roster changes and trades. Reddit 2.pdf discusses team composition. If no dir...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 1.pdf: post by u/MannerSuperb titled 'Who are teams in the playoffs that have impressed you?' (31 upvotes, 236 comments). This tests user-specific retrieval — the username 'M...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 3.pdf: 'Reggie Miller is the most efficient first option in NBA playoffs' which has HIGHEST engagement (1300 post upvotes, 11515 max comment upvotes). Post engagement boostin...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Post engagement boosting (0-1% based on upvotes) should create ranking: (1) Reddit 3 (1300 upvotes) >> (2) Reddit 2 (457) > (3) Reddit 4 (272) > (4) Reddit 1 (31). Tests post-level boosting. Expect...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Comment upvote boosting (0-2% relative within each post) should prioritize: (1) Reddit 2 comment (756 upvotes), (2) Reddit 4 comment (240 upvotes), (3) Reddit 1 comment (186 upvotes). Within-post r...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should prioritize: (1) NBA official accounts (if present, 2% boost), (2) highly-upvoted comments (756, 240, 186 upvotes from Reddit 2, 4, 1 respectively), (3) high-engagement posts (Reddit 3 with 1...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Query about 'efficiency' should retrieve: (1) Reddit 3 (1300 upvotes, explicitly about efficiency) ranked MUCH HIGHER than (2) Reddit 1 (31 upvotes, mentions efficiency indirectly). Post engagement...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Highly-upvoted comments represent community consensus: (1) Reddit 2 top comment (756 upvotes) about popularity contest, (2) Reddit 4 top comment (240 upvotes) about six teams without home court, (3...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve Reddit 3.pdf (historical playoff efficiency comparison across 20 players) with 1300 upvotes - highest engagement. Contains historical data: Reggie Miller (115 TS%), Kawhi (112%), Cu...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve chunks containing highest-upvoted comments: (1) Reddit 2 (756 upvotes) - fans prefer popularity over basketball quality, (2) Reddit 4 (240 upvotes) - six teams below 4 seed never ha...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='NBA official accounts (is_nba_official=1) receive 2% boost. Expected: If NBA official chunks exist in vector store, they rank in top 3 results regardless of lower semantic similarity. If NO NBA off...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve regular NBA.xlsx (glossary/reference document), NOT Reddit discussions. Expected definition: Pick and roll is an offensive play where a player sets a screen (pick) and then moves to...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve regular NBA.xlsx glossary defining PER (Player Efficiency Rating) as an advanced statistic measuring per-minute performance. Glossary should rank HIGHEST (85-95% similarity). If Red...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve regular NBA.xlsx glossary. Expected definition: Zone defense is a defensive strategy where players guard court areas/zones rather than specific opponents. Glossary should rank HIGHE...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve regular NBA.xlsx glossary. Expected definition: True Shooting Percentage (TS%) accounts for 2-pointers, 3-pointers, and free throws in efficiency calculation. May include formula: T...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve regular NBA.xlsx glossary. Expected definition: Triple-double means achieving double-digit totals (10+) in three statistical categories in a single game (e.g., points, rebounds, ass...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve regular NBA.xlsx glossary, NOT Reddit discussions. Expected definition: Man-to-man = each defender guards specific opponent; Zone defense = defenders guard court areas/zones. Glossa...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve regular NBA.xlsx glossary chunks defining multiple efficiency metrics: TS% (True Shooting %), eFG% (Effective Field Goal %), PER (Player Efficiency Rating), usage rate. May retrieve...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="May retrieve: (1) regular NBA.xlsx glossary definition if available ('first option = team's primary scorer/go-to offensive player'), or (2) Reddit 3.pdf contextual usage ('Reggie Miller is the most...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Out-of-scope query. Vector search WILL retrieve irrelevant chunks (likely Reddit PDFs with ~65-70% similarity due to semantic overlap with 'Los Angeles'). However, LLM should recognize retrieved co...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Out-of-scope query. Vector search WILL retrieve irrelevant Reddit chunks with ~62-68% similarity (weakest match due to no semantic overlap). LLM should recognize content is basketball-related, NOT ...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Out-of-scope query. Vector search WILL retrieve irrelevant Reddit chunks (likely Reddit 1-4 with ~68-72% similarity due to semantic overlap with 'results', 'latest'). However, LLM should recognize ...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Out-of-scope query. Vector search WILL retrieve irrelevant chunks (~63-68% similarity). LLM should recognize content is basketball-related, NOT financial data, and respond with 'I don't have inform...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Out-of-scope query. Vector search WILL retrieve basketball-related chunks (~72-78% similarity due to 'NBA' keyword match), possibly Reddit discussions about strategies. However, LLM should recogniz...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Out-of-scope query. Vector search WILL retrieve irrelevant chunks (~60-67% similarity - very weak). LLM should recognize content is basketball-related, NOT tech support, and respond with 'I don't h...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Out-of-scope query. Vector search WILL retrieve irrelevant chunks (~64-69% similarity, possibly New York Knicks mentions). LLM should recognize content is basketball-related, NOT restaurant recomme...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Single punctuation mark is not meaningful query. Vector search WILL retrieve random chunks (~55-65% similarity - very weak, essentially random). LLM should recognize lack of coherent question and r...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Random keyboard mashing. Vector search WILL retrieve random chunks (~50-60% similarity - essentially random match). LLM should recognize lack of coherent query intent and respond with 'I don't unde...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Out-of-scope (cosmology) + unreasonable request (10000 words). Vector search WILL retrieve irrelevant chunks (~65-70% similarity due to 'history'). LLM should: (1) recognize topic is out of scope (...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Out-of-scope query (translation service). Vector search WILL retrieve irrelevant chunks (~60-68% similarity - weak match). LLM should recognize content is basketball-related, NOT translation servic...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="XSS injection attempt + legitimate query. System should: (1) sanitize/escape HTML tags (no script execution), (2) extract legitimate query portion ('Who won the MVP?'), (3) respond about MVP if dat...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='SQL injection attempt. System should: (1) treat as literal text string, NOT SQL command, (2) not execute any database operations, (3) vector search processes it as gibberish text (~55-65% similarit...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Path traversal attempt. System should: (1) treat as literal text, NOT file path, (2) not access file system, (3) vector search processes as text string (~50-60% similarity - essentially random). LL...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Template injection attempts (Jinja, JavaScript, ERB). System should: (1) treat as literal text, NOT execute templates, (2) no evaluation of expressions (result should NOT be '49'), (3) vector searc...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Excessively long input (10,000 'A' characters). System should: (1) handle gracefully without crashing, (2) possibly truncate input to reasonable length (e.g., first 500-1000 chars), or (3) reject w...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit discussions mentioning Lakers. Most likely source: Reddit 4.pdf mentions '2020 Lakers' as example of team without home court advantage in Finals. May also appear in Reddit 1 ...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Follow-up question referencing 'their' = Lakers from Turn 1. System should: (1) maintain conversation context (Lakers = subject), (2) retrieve Lakers-specific content about strengths. Expected sour...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Second follow-up still referencing Lakers from Turn 1 and 2. System should: (1) maintain conversation context across THREE turns, (2) retrieve Lakers content about weaknesses/limitations. Expected ...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 1.pdf: 'Who are teams in the playoffs that have impressed you?' discussing Magic (Paolo/Franz), Wolves (Ant), Pacers, Pistons. Top comment (186 upvotes) about Ant being a mac...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Follow-up referencing 'they' = surprising teams from Turn 1 (Magic, Wolves, Pacers, Pistons). System should: (1) maintain context of which teams were mentioned, (2) retrieve Reddit 1.pdf chunks exp...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Third-level follow-up referencing 'them' = surprising teams from Turn 1-2. System should: (1) maintain conversation context across THREE turns, (2) retrieve content comparing underdogs (Magic, Wolv...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve Reddit 3.pdf discussing playoff efficiency metrics: TS% (True Shooting %), scoring volume, comparison of 20 players. Expected definition: efficiency = high TS% (115% for Miller, 112...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Follow-up asking for specific player. Should retrieve Reddit 3.pdf: 'Reggie Miller is the most efficient first option in NBA playoff history' (1300 upvotes). Post engagement boosting should rank Re...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Second follow-up referencing 'his' = Reggie Miller from Turn 2. System should: (1) maintain context across THREE turns (efficiency → Reggie Miller → debate about him), (2) retrieve Reddit 3.pdf com...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 4.pdf: 'Which NBA team did not have home court advantage until the NBA Finals?' (272 upvotes, 51 comments). Top answer (240 upvotes): Six teams below 4 seed never had home co...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="TOPIC SWITCH from home court (Turn 1) back to efficiency. Phrase 'Going back to' indicates explicit topic change. System should: (1) recognize topic switch, (2) retrieve Reddit 3.pdf efficiency dis...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="SECOND topic switch, back to home court from Turn 1. Phrase 'Returning to' indicates explicit topic change. System should: (1) recognize topic switch back to home court, (2) retrieve Reddit 4.pdf w...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Noisy query with typos and text-speak. Should map to: 'Who is the best player in playoffs according to Reddit?'. Should retrieve Reddit discussions mentioning top players: Ant (Anthony Edwards) fro...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Heavy typos but clear intent: 'Reggie Miller efficiency debate'. Should retrieve Reddit 3.pdf: 'Reggie Miller is the most efficient first option in NBA playoffs' (1300 upvotes). Vector search shoul...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Informal slang expressing opinion about surprising playoff teams. Should map to Reddit 1.pdf: 'Who are teams in the playoffs that have impressed you?' discussing Magic, Wolves, Pacers, Pistons. Vec...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Abbreviations + informal grammar expressing opinion on home court advantage. Should map to Reddit 4.pdf discussing home court importance. Vector search should: (1) expand abbreviations (imho='in my...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Keyword stuffing/repetition but clear intent: 'playoff teams impressive'. Should map to Reddit 1.pdf: 'Who are teams in the playoffs that have impressed you?'. Vector search should handle repetitio...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Extremely vague query with excessive punctuation. Vector search WILL retrieve random Reddit chunks (~68-75% similarity). LLM should: (1) recognize query is too vague, AND (2) either ask 'What speci...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Casual slang asking about top teams. Should map to Reddit 2.pdf: 'How is it that the two best teams in the playoffs...' (457 upvotes). Vector search should understand: 'yo what'='what are', 'ppl'='...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Single word, extremely vague. Vector search WILL retrieve random Reddit chunks (~65-75% similarity - all have 'nba' keyword). LLM should recognize query lacks specificity and respond with: 'What wo...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Non-question greeting input. Vector search WILL retrieve random chunks (~60-70% similarity - weak semantic match). LLM should recognize this is a greeting, not a question, and respond with somethin...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Complex multi-document synthesis query. Should retrieve chunks from: (1) Reddit 1 (young talent strategies: Magic with Paolo/Franz, Wolves with Ant), (2) Reddit 2 (discussion of stats-based vs popu...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Meta-analysis requiring identification of recurring themes across ALL 4 Reddit posts. Patterns: (1) Efficiency metrics emphasis (Reddit 3: TS%, comparison tables), (2) Surprising/impressive teams (...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Requires contrasting qualitative opinions vs quantitative stats. Should retrieve: (1) Reddit 3.pdf quantitative table (Miller 115 TS%, Kawhi 112%, etc.) showing STATISTICAL measures, AND (2) Reddit...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should identify debated topics across multiple Reddit posts: (1) Reddit 3: Is TS% the right efficiency metric? Era-adjusted vs raw stats, (2) Reddit 4: Does home court advantage really matter? Six ...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='High-level synthesis requiring integration from ALL 4 Reddit posts. Success factors: (1) Reddit 1: Young talent development (Paolo, Franz, Ant), exceeding expectations, (2) Reddit 2: Statistical ex...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve Reddit discussions about playoff strategies and team approaches. Reddit 1.pdf discusses what makes teams impressive (young talent, team composition). Reddit 3.pdf discusses offensiv...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Should retrieve Reddit discussions referencing NBA history and evolution. Reddit 3.pdf contains historical playoff efficiency comparison across 20 players spanning different eras (Reggie Miller, Jo...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Mixed query combining statistical ask ('how many points') with opinion ask ('why do fans love him'). For vector evaluation, the system should retrieve Reddit discussions mentioning LeBron. Reddit 1...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth='Sentiment analysis across all 4 Reddit posts: (1) Reddit 1 (31 upvotes): Positive sentiment — excitement about impressive teams (Magic, Wolves), admiration for young talent. (2) Reddit 2 (457 upvot...',
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth="Should retrieve Reddit 3.pdf containing direct quotes about efficiency. Key quotes: (1) Post title: 'Reggie Miller is the most efficient first option in NBA playoff history' by u/hqppp. (2) Top com...",
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer=None,

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Shai Gilgeous-Alexander scored 2485 points. His effectiveness comes from his ability to get to the rim and draw fouls.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='LeBron James: 1708 PTS. Kevin Durant: 1649 PTS. LeBron uses strength and playmaking while Durant relies on elite shooting.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Jokić averages 29.6 PPG (2072 PTS in 70 GP). He's elite because of his versatile scoring, exceptional passing, and high basketball IQ.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 3: Ivica Zubac (1008), Domantas Sabonis (973), Karl-Anthony Towns (922). They create second-chance opportunities and control the boards.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Jokić: 2072 PTS, 889 REB, 714 AST (PIE: 20.6). Embiid: 452 PTS, 156 REB, 86 AST (PIE: 16.9). Jokić excels in playmaking while Embiid dominates with scoring and defense.',

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Who are the most efficient scorers by true shooting percentage and what makes them efficient?',
        test_type=TestType.HYBRID,
        category='tier2_efficiency_analysis',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ts_pct, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 ORDER BY ps.ts_pct DESC LIMIT 5',
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top efficient scorers have high TS% because of good shot selection, high free throw rates, and effective three-point shooting.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Giannis: 797 REB. Davis: 592 REB. Giannis uses length and athleticism for rebounds, while Davis combines timing and positioning.',

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Who has the best assist-to-turnover ratio among high-volume passers and why is this important?',
        test_type=TestType.HYBRID,
        category='tier2_efficiency_metric',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.ast, ps.tov, ROUND(ps.ast*1.0/ps.tov, 2) as ratio FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.ast >= 300 AND ps.tov > 0 ORDER BY (ps.ast*1.0/ps.tov) DESC LIMIT 5',
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='High AST/TO ratio indicates excellent decision-making and ball security, crucial for winning basketball by maximizing possessions.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Nikola Jokić averages 29.6/12.7/10.2. Triple-doubles require elite versatility in scoring, rebounding, and playmaking - a rare combination.',

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which players have high scoring but low efficiency, and why might teams still rely on them?',
        test_type=TestType.HYBRID,
        category='tier3_strategic_tradeoff',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.fg_pct, ps.ts_pct FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 1500 AND ps.fg_pct < 45 ORDER BY ps.pts DESC',
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='High-volume low-efficiency scorers may still be valuable due to clutch performance, defensive attention they draw, or lack of other offensive options.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 defenders: Dyson Daniels (228 STL, 53 BLK), Victor Wembanyama (51 STL, 175 BLK), Shai Gilgeous-Alexander (129 STL, 76 BLK), Myles Turner (58 STL, 144 BLK), Jaren Jackson Jr. (89 STL, 111 BLK). Daniels excels at perimeter defense while Wembanyama is an elite rim protector.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top dual-threat players: Shai Gilgeous-Alexander (2485 PTS, 486 AST), Anthony Edwards (2180 PTS, 356 AST), Nikola Jokić (2072 PTS, 714 AST), Giannis Antetokounmpo (2037 PTS, 436 AST), Jayson Tatum (1930 PTS, 432 AST). These scorers and playmakers force defenses to make difficult choices, creating advantages for teammates while maintaining personal scoring threat.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Modern NBA emphasizes three-point shooting due to analytics showing its efficiency. The 'three-point revolution' has changed offensive strategies and floor spacing.",

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Compare advanced efficiency metrics (PIE, TS%) for MVP candidates and explain what these metrics reveal about player impact.',
        test_type=TestType.HYBRID,
        category='tier4_advanced_metrics_interpretation',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pie, ps.ts_pct, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.pts > 1800 ORDER BY ps.pie DESC LIMIT 5',
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='PIE measures overall player impact while TS% captures scoring efficiency. Together they reveal both productivity and effectiveness in generating value.',

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question="How do young players (high stats) compare to established stars, and what does this suggest about the league's future?",
        test_type=TestType.HYBRID,
        category='tier4_generational_shift',

        # SQL Expectations
        expected_sql='SELECT p.name, p.age, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.age IS NOT NULL ORDER BY ps.pts DESC LIMIT 10',
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Young stars with elite stats suggest a generational talent shift, with younger players developing skills faster through modern training and analytics.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 5 high-assist players: Trae Young (882 AST, PIE 12.9), Nikola Jokić (714 AST, PIE 20.6), James Harden (687 AST, PIE 14.5), Tyrese Haliburton (672 AST, PIE 14.3), Cade Cunningham (637 AST, PIE 15.2). High-assist players facilitate team offense by creating efficient shot opportunities for teammates.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Warriors average 487.5 points per player across 17 players. Fan discussions describe their culture as built on ball movement and championship pedigree.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Giannis Antetokounmpo: 2037 PTS, 797 REB, 436 AST (PIE 21.0). Nikola Jokić: 2072 PTS, 889 REB, 714 AST (PIE 20.6). Fan opinions are split between Giannis's dominance and Jokić's versatility.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="LeBron James (age 40, Los Angeles Lakers): 1708 PTS, 546 REB, 574 AST, 70 STL, 42 BLK in 70 GP (24.4 PPG). FG%: 51.3%, 3P%: 37.6%, FT%: 78.2%. Reddit fans describe LeBron as the NBA's biggest superstar brand who drives media narratives. He ranks among the all-time playoff greats (8289 career playoff PTS, 107 TS). Fans note his dangerous ISO game, elite playmaking, and shots near the rim make him a hybrid threat. Some debate whether AD was more impactful during their title run despite LeBron's popularity.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Anthony Edwards (age 23, Timberwolves): 2180 PTS, 450 REB, 356 AST in 79 GP (27.6 PPG). His explosiveness and scoring versatility make him one of the league's most exciting players.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Victor Wembanyama (age 21): 1118 PTS, 506 REB, 175 BLK in 46 GP. His combination of size, shot-blocking, and offensive skill at such a young age has fans calling him a generational talent.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Trae Young: 1839 PTS, 882 AST, 41.1% FG, 357 TOV. Fan debate centers on whether his elite playmaking outweighs his low efficiency and turnovers.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Cade Cunningham (age 23, Pistons): 1827 PTS, 427 REB, 637 AST in 70 GP. Fans view him as a franchise cornerstone whose all-around game is improving each season.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Celtics: 9551 PTS, 3723 REB, 2147 AST. Lakers: 8691 PTS, 3321 REB, 2135 AST. The Celtics are statistically dominant while the Lakers rely more on star power.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Nuggets: 9899 PTS (582.3 avg), 2538 AST. Thunder: 9880 PTS (548.9 avg), 2195 AST. Both are elite, with fans debating whether Denver's experience or OKC's youth gives the edge.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='OKC leads with 1298 defensive actions (840 STL, 458 BLK). Fan discussions praise their aggressive perimeter defense and switchability.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Pacers: 9630 total PTS (481.5 avg), 2395 AST. Fans admire their fast-paced, team-oriented offense and balanced scoring.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top young stars under 25: Anthony Edwards (23, 2180 PTS), Cade Cunningham (23, 1827), Jalen Green (23, 1722), Jalen Williams (24, 1490), Alperen Sengun (22, 1452). Fans see this generation as ready to take over the league.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top under-22 players: Alperen Sengun (22, 1452), Shaedon Sharpe (22, 1332), Paolo Banchero (22, 1191), Stephon Castle (20, 1191), Bennedict Mathurin (22, 1159). Fans are excited about their development trajectories.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top veterans (35+): Harden (35, 1801), Curry (37, 1715), DeRozan (35, 1709), LeBron (40, 1708), Durant (36, 1649). Fans debate whether these legends can still compete with the young wave.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='2000+ point scorers: SGA (2485, 32.7 PPG), Edwards (2180, 27.6), Jokić (2072, 29.6), Giannis (2037, 30.4). Reddit discusses playoff efficiency legends like Reggie Miller (115 TS%), providing historical context.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Top current TS%: Jarrett Allen (72.4%), Christian Braun (66.5%), Jokić (66.3%), Harrison Barnes (65.6%), Domantas Sabonis (65.5%). Reddit discusses Reggie Miller's 115 TS% in playoffs, putting modern efficiency in perspective.",

        # Optional: Conversation context
        conversation_thread=None,
    ),
    UnifiedTestCase(
        question='Which current players match the historical playoff dominance that fans discuss on Reddit?',
        test_type=TestType.HYBRID,
        category='hybrid_historical',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 ORDER BY ps.pie DESC LIMIT 5',
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Current dominant players (Giannis, Jokić, SGA) produce historically elite numbers. Reddit's discussions about playoff efficiency legends provide context for evaluating today's stars.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='High-volume low-efficiency: Edwards (2180 PTS, 44.7% FG), Young (1839, 41.1%), Harden (1801, 41.0%), Green (1722, 42.3%), Curry (1715, 44.8%). Fans debate whether volume scoring with lower efficiency is acceptable given their shot creation.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Trae Young leads in assists (882) but also turnovers (357). Fan discussions debate whether his elite playmaking compensates for turnovers.',

        # Optional: Conversation context
        conversation_thread=None,
    ),

    UnifiedTestCase(
        question='Are there players with modest scoring but exceptional all-around impact, and what does this reveal about value?',
        test_type=TestType.HYBRID,
        category='hybrid_contrast',

        # SQL Expectations
        expected_sql='SELECT p.name, ps.pts, ps.pie FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE ps.gp > 50 AND ps.pie > 15 ORDER BY ps.pie DESC LIMIT 5',
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='High PIE players include some beyond just top scorers. PIE captures overall impact — scoring, rebounding, assists, defensive actions — revealing value beyond the box score.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Shai Gilgeous-Alexander: 2485 PTS, 380 REB, 486 AST, 51.9% FG in 76 GP.',

        # Optional: Conversation context
        conversation_thread='mvp_sga_discussion',
    ),
    UnifiedTestCase(
        question='Why do fans on Reddit consider him an MVP favorite?',
        test_type=TestType.HYBRID,
        category='hybrid_conversational_mvp',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pie, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.name LIKE '%Shai%'",
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="SGA's combination of elite scoring (2485 PTS), efficiency (51.9% FG), and team success makes him a top MVP candidate. Fan discussions highlight his complete game and leadership.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="SGA: 63.7% TS, 56.9% EFG, 19.9 PIE. Reddit debates about historical playoff efficiency (Reggie Miller 115 TS%, Kawhi 112%) provide context — SGA's efficiency is elite by any era's standards.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Celtics: 9551 total PTS (561.8 avg), 3723 REB, 2147 AST across 17 players.',

        # Optional: Conversation context
        conversation_thread='team_celtics_deepdive',
    ),
    UnifiedTestCase(
        question='What do fans think about their chances of repeating as champions?',
        test_type=TestType.HYBRID,
        category='hybrid_conversational_team',

        # SQL Expectations
        expected_sql="SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id WHERE p.team_abbr = 'BOS' ORDER BY ps.pts DESC LIMIT 3",
        ground_truth_data=None,

        # Vector Expectations
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Fan discussions weigh the Celtics' depth and balanced scoring. With Tatum, Brown, and White leading, fans debate whether their roster continuity gives them an edge in repeating.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Nuggets: 9899 PTS (582.3 avg) vs Celtics: 9551 PTS (561.8 avg). Denver edges Boston in scoring, but fans note the Celtics' defensive advantages.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Shai Gilgeous-Alexander leads with 2485 PTS. Reddit fans praise his complete game and consider him the top player this season.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='LeBron James: 1708 PTS, 546 REB, 574 AST. At age 40, fans marvel at his longevity and debate his legacy as one of the greatest ever.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer="Jokić: 2072 PTS, 714 AST. Curry: 1715 PTS, 420 AST. Fan opinions split between Curry's revolutionary shooting and Jokić's all-around dominance.",

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Victor Wembanyama leads with 175 BLK (plus 1118 PTS, 506 REB). Fans consider his shot-blocking a generational skill combining elite length with instinctive timing.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top PIE: Giannis (21.0), Jokić (20.6), SGA (19.9), Davis (17.9), LeBron (16.9). PIE captures total impact — fans increasingly value this over raw scoring.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top 3 assists: Trae Young (882, 11.6 APG), Nikola Jokić (714, 10.2 APG), James Harden (687, 8.7 APG). Fans discuss how playmaking has evolved from traditional PG skills to big-man facilitating.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Thunder: 9880 PTS (548.9 avg), 3660 REB, 2195 AST across 18 players. Fans describe OKC as young, athletic, and defensively relentless.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Timberwolves: 9523 PTS (476.1 avg), 3656 REB, 2175 AST across 20 players. Led by Anthony Edwards, fans see them as a legitimate contender.',

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
        ground_truth=None,
        min_vector_sources=0,
        expected_source_types=None,

        # Answer Expectations
        ground_truth_answer='Top by 3PA: Edwards (814, 39.5%), Curry (784, 39.7%), Beasley (763, 41.6%). Fan discussions highlight how three-point shooting has fundamentally changed offensive strategy.',

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
    print(f"Total test cases: {stats['total']}")
    print(f"  SQL: {stats['sql']}")
    print(f"  Vector: {stats['vector']}")
    print(f"  Hybrid: {stats['hybrid']}")
