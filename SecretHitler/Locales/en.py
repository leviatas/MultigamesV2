# -*- coding: utf-8 -*-
"""Secret Hitler bot texts in English.

Keys must match SecretHitler/Locales/es.py exactly (es.py is the reference catalog;
i18n.t() falls back to it for any key missing here).

Templates keep the placeholders used by the calling code: some use %s/%d (percent
formatting), others {} or {name} (str.format). Keep the placeholders and their order.
"""

TEXTS = {}

# --- Game in progress: rounds, votes, powers and endgame (MainController) ----------
TEXTS.update({
    'anarchy.announce': 'ANARCHY!!',
    'anarchy.approved': 'Since most players decided to go to anarchy, anarchy is executed.',
    'anarchy.ask': 'Do you want to go to anarchy? (CAREFUL: if half the players say yes, we go without waiting)',
    'anarchy.change_ask': 'You can change your vote here.\nDo you want to go to anarchy? (CAREFUL: if half the players say yes, we go without waiting)',
    'anarchy.rejected': 'Nobody wanted to go to anarchy',
    'anarchy.top_enacted': 'The policy on top of the deck has been enacted and it is %s',
    'anarchy.vote_thanks': 'Thanks for your vote: %s for anarchy',
    'chairman.choose_prompt': 'Choose the Chairman. They get to peek at the top policy of the deck!',
    'chairman.chosen_announce': 'Chancellor %s chose %s as Chairman.',
    'chairman.must_choose': 'Chancellor %s has to choose the Chairman ',
    'chairman.nobody_available': 'There is no player available to be Chairman, so we go straight to the legislative session.',
    'chairman.not_chancellor': 'You are not the current chancellor, you cannot choose!',
    'chairman.peek': '%s\nYou peeked at the top policy of the deck: *%s*',
    'chairman.peek_hidden': 'Chairman %s peeked at %s',
    'chairman.you_chose': 'You chose %s as Chairman!',
    'chancellor.nominate_prompt': 'Please nominate your chancellor!',
    'chancellor.nominate_prompt_group': '{}Please nominate your chancellor!',
    'chancellor.nominated_announce': 'President %s nominated %s as chancellor. Please vote now!',
    'chancellor.not_president': 'You are not the current president, you cannot nominate!',
    'chancellor.you_nominated': 'You nominated %s as chancellor!',
    'choose.announce': 'President %s has chosen %s as the next president.',
    'choose.you_chose': 'You have chosen %s as the next president!',
    'cmd.all.group_only': 'This command only works in a group.',
    'cmd.all.header': '\U0001F4E2 *Everyone, listen up!*\n',
    'cmd.all.no_members': "I don't have any known members of this group yet. They get registered as they join or leave the group, or when they join a game with /join.",
    'common.in_group': '*In the group {}*\n',
    'end.cancelled': 'Game cancelled!',
    'end.cancelled_with_roles': 'Game cancelled!\n\n%s',
    'end.fascists_win_hitler': 'Game over! The fascists won by electing Hitler as Chancellor!\n\n%s',
    'end.fascists_win_policies': 'Game over! The fascists won by enacting 6 fascist policies!\n\n%s',
    'end.liberals_win_kill': 'Game over! The liberals won by killing Hitler!\n\n%s',
    'end.liberals_win_policies': 'Game over! The liberals won by enacting 5 liberal policies!\n\n%s',
    'end.mvp_invite': '\U0001F3C5 You can now use /mvp to privately vote for the MVP of this game! The result is revealed once every player has voted.',
    'end.prueba_notice': '\U0001F9EA *Test game*: no stats were saved, no achievements were granted and there is no MVP vote.\nThe next game counts again (or use /prueba so it does not count either).',
    'end.socialists_win': 'Game over! The socialists won by enacting their whole socialist track!\n\n%s',
    'error.set_stats_failed': 'The set_stats command failed because of: ',
    'hidden.president_discarded': 'The president discarded ',
    'hidden.president_drew': '*Round %d.%d*\nPresident %s drew ',
    'hidden.remaining_policies': '\nPolicies left in the deck:\n',
    'hidden.title': 'Hidden History:\n\n',
    'history.round_header': 'Round %d.%d\n\n',
    'inspect.announce': 'President %s has investigated %s.',
    'inspect.result': "%s's party membership is %s",
    'kill.hitler_announce': 'President %s has killed %s. ',
    'kill.not_hitler_announce': 'President %s has killed %s, who was not Hitler. %s, you are dead now and cannot talk any more!',
    'kill.not_hitler_history': 'President %s has killed %s, who was not Hitler!',
    'kill.you_are_dead': '{}YOU ARE DEAD, %s HAS KILLED YOU',
    'kill.you_killed': 'You have killed %s!',
    'legis.choose_enact': 'President %s handed you the following 2 policies. Which one do you want to enact?',
    'legis.choose_enact_with_veto': 'President %s handed you the following 2 policies. Which one do you want to enact? You can also use the Veto power.',
    'legis.draw_prompt': '\nYou drew the following 3 policies. Which one do you want to discard?',
    'legis.enacted_announce': 'President %s and Chancellor %s enacted a %s policy!',
    'legis.not_president_nor_chancellor': 'You are neither the current president nor the current chancellor!',
    'legis.passed_two': 'President %s handed two policies to Chancellor %s.',
    'legis.policy_will_be_enacted': 'The %s policy will be enacted!',
    'legis.veto_refused_choose': 'President %s rejected your Veto. Now you have to choose. Which one do you want to enact?',
    'legis.you_drew_discard': 'You drew %s. The %s policy will be discarded!',
    'power.choose_body': '\nPresident %s can choose the next presidential candidate. After that the order continues as usual.',
    'power.choose_prompt': 'You can choose the next presidential candidate. After that the order goes back to normal. Choose wisely!',
    'power.choose_title': 'Presidential Power unlocked: Call Special Election ',
    'power.inspect_body': "\nPresident %s can see a player's party membership. The President may share (or lie about!) the results of the investigation at their own discretion.",
    'power.inspect_prompt': "You can see a player's party membership. Who do you want to choose? Choose wisely!",
    'power.inspect_title': 'Presidential Power unlocked: Investigate Loyalty ',
    'power.kill_body': '\nPresident %s has to execute someone. You can discuss the decision now but the President has the last word.',
    'power.kill_prompt': 'You have to execute someone. You can discuss your decision with the others. Choose wisely!',
    'power.kill_title': 'Presidential Power unlocked: Execution ',
    'power.policy_body': '\nPresident %s now knows the next three policies in the deck. The President may share (or lie about!) the results of the investigation at their own discretion.',
    'power.policy_history': 'President %s now knows the next 3 policies in the deck.',
    'power.policy_peek_result': 'The next 3 policies are (the top one comes first):\n%s\nYou can lie about it if you want.',
    'power.policy_title': 'Presidential Power unlocked: Policy Peek ',
    'round.next_president': 'The next presidential candidate is [%s](tg://user?id=%d).\n%s, please nominate a chancellor in our private chat!',
    'setup.roles_10': 'There are 6 Liberals, 3 Fascists and Hitler. Hitler does not know who the Fascists are.',
    'setup.roles_5': 'There are 3 Liberals, 1 Fascist and Hitler. Hitler knows who the Fascist is.',
    'setup.roles_6': 'There are 4 Liberals, 1 Fascist and Hitler. Hitler knows who the Fascist is.',
    'setup.roles_7': 'There are 4 Liberals, 2 Fascists and Hitler. Hitler does not know who the Fascists are.',
    'setup.roles_8': 'There are 5 Liberals, 2 Fascists and Hitler. Hitler does not know who the Fascists are.',
    'setup.roles_9': 'There are 5 Liberals, 3 Fascists and Hitler. Hitler does not know who the Fascists are.',
    'setup.roles_socialista': 'There are %d Liberals, %d Fascists, Hitler and %d Socialists. Hitler does not know anyone.',
    'shuffle.announce': 'There were not enough cards left in the policy deck, so I shuffled the rest together with the discard pile!',
    'shuffle.guess_reminder': '🔮 Remember you can use /guess to try to figure out what each player is! It happens in private and is revealed at the end of the game.',
    'shuffle.history': '*There were not enough cards left in the policy deck, so I shuffled the rest together with the discard pile!*',
    'soc.btn_agree': 'Yes, I agree',
    'soc.censorship_announce': ' Censorship: from now on the Chancellor no longer picks a Chairman.',
    'soc.censorship_history': 'Censorship kicked in: no more Chairman.',
    'soc.confesion_announce': 'President %s confessed their party membership to %s.',
    'soc.confesion_body': '\nPresident %s has to show their party membership to whoever the socialists pick.',
    'soc.confesion_pick': " *Confession*: propose who gets to see President %s's party membership.",
    'soc.confesion_result': " *Confession*: President %s's party membership is *%s*.",
    'soc.confesion_skip_body': '\nThere is no president this round, so the power is skipped.',
    'soc.confesion_skip_title': 'Socialist Power: Confession ',
    'soc.confesion_title': 'Socialist Power unlocked: Confession ',
    'soc.congreso_body': '\nThe socialists recognise each other.',
    'soc.congreso_hidden': 'Congress: socialists of origin %s / new ones %s',
    'soc.congreso_history': 'The socialist party used the Congress.',
    'soc.congreso_new': ' *Congress*: the new socialist is *%s*.',
    'soc.congreso_none_recruited': ' *Congress*: you have not recruited anyone yet, so there are no new socialists.',
    'soc.congreso_originals': ' *Congress*: the socialists of origin are *%s*.',
    'soc.congreso_title': 'Socialist Power unlocked: Congress ',
    'soc.congreso_was_hitler': ' *Congress*: there is no new socialist, so the person you recruited was *Hitler*.',
    'soc.decision_resolved': 'That decision is already settled.',
    'soc.escucha_body': "\nThe socialists are going to see a player's party membership. Nobody else finds out who they picked.",
    'soc.escucha_hidden': 'The socialists bugged %s (%s)',
    'soc.escucha_pick': ' *Illegal Bug*: propose whose party membership you want to see.',
    'soc.escucha_result': " Illegal Bug: %s's party membership is *%s*",
    'soc.escucha_title': 'Socialist Power unlocked: Illegal Bug ',
    'soc.escucha_used_group': 'The socialists have already used their Illegal Bug.',
    'soc.escucha_used_history': 'The socialists used their Illegal Bug.',
    'soc.nobody': 'nobody',
    'soc.none': 'none',
    'soc.party_agreed': 'The party agreed on *%s*.',
    'soc.plan_body': '\n2 socialist policies and 1 liberal one were added to the deck, and it was shuffled. There are %d policies left now.',
    'soc.plan_title': 'Socialist Power unlocked: Five-Year Plan ',
    'soc.power_skipped': 'The socialist power cannot be used and is skipped.',
    'soc.proposal_ask': '%s\n%s proposes *%s* for the socialist power. Do you agree?\n*Every* socialist has to agree.',
    'soc.proposal_in_progress': 'There is already a proposal in progress, or the power was already used.',
    'soc.proposal_waiting': 'You proposed *%s*. Waiting for the rest of the party to agree...',
    'soc.reclutamiento_body': '\nThe socialists are going to convert a player. When they are done, check your party membership with /info: if it changed, you now win with the socialists.',
    'soc.reclutamiento_pick': ' *Recruitment*: propose who you want to convert into a socialist.',
    'soc.reclutamiento_title': 'Socialist Power unlocked: Recruitment ',
    'soc.recruited_dm': ' *You have been recruited by the socialists!* From now on your party membership is socialist and you win with them. Your role and everything you knew stay the same.',
    'soc.recruited_hidden': 'The socialists recruited %s',
    'soc.recruited_hitler_dm': ' The socialists recruited you, but you are *Hitler*: it does not work on you. Keep acting as if nothing happened, you still win with the fascists and you take no part in their decisions. That said, you now hold the socialist card, so anyone who investigates you will see *socialist*.',
    'soc.recruited_hitler_hidden': 'The socialists recruited %s, who was Hitler: he keeps the socialist card but is still a fascist.',
    'soc.recruitment_chosen': ' Recruitment: the party chose *%s*.',
    'soc.recruitment_used_group': 'The socialists have already used their Recruitment. Check your party membership with /info!',
    'soc.recruitment_used_history': 'The socialists used their Recruitment.',
    'soc.someone_rejected': 'A socialist *did not agree* with %s. Pick again.',
    'soc.waiting_plural': '%d socialists still have to answer about %s.',
    'soc.waiting_singular': '%d socialist still has to answer about %s.',
    'soc.you_accepted': "You accepted %s's proposal.",
    'soc.you_proposed_confesion': " You proposed that %s sees the President's party membership.",
    'soc.you_proposed_escucha': ' You proposed bugging %s.',
    'soc.you_proposed_reclutamiento': ' You proposed recruiting %s.',
    'soc.you_rejected': "You rejected %s's proposal.",
    'start.begin_game': 'We are starting the game with %d players!\n%s\nGo to our private chat and look at your secret role!',
    'veto.accepted_announce': "President %s accepted Chancellor %s's Veto. No policy was enacted, but this counts as a failed election.",
    'veto.ask_president': 'Chancellor %s suggested a Veto. Do you want to veto (discard) these cards?',
    'veto.btn_no': 'No Veto! (reject the suggestion)',
    'veto.btn_veto': 'Veto',
    'veto.btn_yes': 'Veto! (accept the suggestion)',
    'veto.rejected_announce': "President %s rejected Chancellor %s's Veto. The Chancellor must now choose a policy!",
    'veto.suggested_announce': 'Chancellor %s suggested vetoing President %s.',
    'veto.you_accepted': 'You have accepted the Veto!',
    'veto.you_rejected': 'You have rejected the Veto!',
    'veto.you_suggested': 'You have suggested vetoing President %s',
    'vote.ask_group': '{}Do you want to elect President *{}* and chancellor *{}*?',
    'vote.autoja_registered': '\n\nYou have */startautoja* on: your *Ja* vote was registered automatically. Use /retirar if you want to vote differently.',
    'vote.change_ask_group': '{}\nYou can change your vote here.\nDo you want to elect President *{}* and chancellor *{}*?',
    'vote.hail': 'Hail President [%s](tg://user?id=%d)! Hail Chancellor [%s](tg://user?id=%d)!',
    'vote.no_talking': '\nNo talking now.',
    'vote.not_voting_time': 'It is not time to vote!',
    'vote.rejected': 'The people did not like President %s and chancellor %s!',
    'vote.summary_all_ja': 'Ja votes: Everyone',
    'vote.summary_all_nein': 'Nein votes: Everyone',
    'vote.summary_ja': '%d Ja votes',
    'vote.summary_nein': '\n%d Nein votes',
    'vote.thanks': 'Thanks for your vote: %s for President %s and chancellor %s',
    'vote.voted_ja_suffix': ' voted Ja!\n',
    'vote.voted_nein_suffix': ' voted Nein!\n',
})

# --- Commands: setup, joining, history, stats (Commands) ---------------------------
TEXTS.update({
    'anarchy.must_be_player': 'You have to be a player in the game to call for anarchy.',
    'autoja.choose_game_on': 'Choose the game where you want to turn the automatic Ja vote on',
    'autoja.choose_game_off': 'Choose the game where you want to turn the automatic Ja vote off',
    'autoja.cut_set': 'Done: your automatic *Ja* vote in *{}* stops {}.',
    'autoja.disabled': 'Automatic *Ja* vote turned off in *{}*.',
    'autoja.enabled': 'Automatic *Ja* vote turned on in *{}*: your Ja vote will be registered on its own as soon as a government is proposed, and it stops {}. Use /stopautoja to turn it off.',
    'autoja.vote_registered': 'Your *Ja* vote for the vote in progress has been registered.',
    'autoja.when_cut_ask': 'When do you want your automatic vote in *{}* to stop?',
    'calltovote.president_must_nominate': 'You cannot vote yet because President [%s](tg://user?id=%d) has not chosen a chancellor. Time to nominate!',
    'calltovote.time_to_vote': 'Time to vote [%s](tg://user?id=%d)!\n',
    'calltovote.wait_five_minutes': 'Five minutes have to go by before you can call for a vote!',
    'cancel.aborted': 'Cancellation aborted, the game goes on.',
    'cancel.btn_yes': 'Yes, cancel the game',
    'cancel.cancelled': 'Game cancelled.',
    'cancel.confirm_ask': 'Are you sure you want to cancel the game? All the game data will be deleted.',
    'cancel.only_creator': 'Only the game creator or a group admin can cancel the game with /cancelgame',
    'cancel.only_requester': 'Only whoever ran /cancelgame can confirm.',
    'claim.added': 'Your claim: %s was added to the history.',
    'claim.added_hidden': 'Your claim: %s was added to the hidden history.',
    'claim.history_line': 'Player %s claims: %s',
    'claim.must_be_player': 'You have to be a player in the game to claim anything.',
    'claim.need_message': 'You have to send a message to make a claim.',
    'claim.need_policy': 'You cannot claim before at least one policy has been enacted.',
    'claim.need_policy_hidden': 'You cannot make a hidden claim before at least one policy has been enacted.',
    'claim.not_in_any_game': 'You cannot make a hidden claim if you are not in any game.',
    'cmd.board.not_started': 'No game has started in this chat. Please start the game with /startgame',
    'cmd.newgame.add_to_group': 'You have to add me to a group first and type /newgame there!',
    'cmd.newgame.already_exists': 'There is already a game in this chat. If you want to end it, type /cancelgame!',
    'cmd.newgame.created': 'New game created! Every player has to join the game with the /join command.\nThe game creator (or the admin) can join too and type /startgame once everybody has joined!',
    'cmd.newgame.created_socialist': ' New game created with the *Socialist Expansion* (%d to %d players)!\nThere is a third party: the socialists win by enacting their whole policy track.\nEvery player has to join the game with the /join command.\nThe game creator (or the admin) can join too and type /startgame once everybody has joined!',
    'cmd.reload.add_to_group': 'You have to add me to a group first and type /reloadgame there!',
    'cmd.version.text': 'Secret Hitler bot v%s',
    'common.datetime_format': '%Y-%m-%d %H:%M',
    'common.game_not_ended': 'The game is not over yet.',
    'common.group_chat_only': 'This command is used in the group chat.',
    'common.group_only': 'This command only works in a group.',
    'common.must_be_player_cmd': 'You have to be a player in the game to use this command.',
    'common.no_active_game_here': 'There is no active game in this chat.',
    'common.no_active_game_there': 'There is no active game in that chat.',
    'common.no_active_games': 'You have no active Secret Hitler games.',
    'common.no_game': 'There is no game in this chat. Create a new one with /newgame',
    'common.no_game_here': 'There is no game in this chat.',
    'common.no_recent_games': 'You have no recently finished games to look at.',
    'common.not_in_game': 'You are not in this game!',
    'common.not_in_that_game': 'You are not in that game.',
    'common.players_so_far': 'The players who have joined so far are:\n',
    'conflicto.announce': '\u26A0\uFE0F The automatic *Ja* vote was turned off for every player in this game. Anyone who wants it back has to use /startautoja again.',
    'conflicto.dm': 'Your automatic *Ja* vote in *{}* was turned off with /conflicto. Use /startautoja if you want it back.',
    'conflicto.nobody_had_it': 'No player had the automatic *Ja* vote turned on.',
    'end.closing_without': 'Closing the MVP vote without waiting for: {}',
    'end.must_be_player': 'You have to be a player in the game to use /end.',
    'end.not_ended': 'The game is not over yet, there is nothing to close.',
    'error.command_failed': 'The command failed because of: ',
    'explain.socialista_1': """\u262D *SOCIALIST EXPANSION* \u262D

You play it with */newgame socialista* (nothing of this changes the classic mode). It is for *{min} to {max} players*.

*THE THIRD PARTY*
Besides liberals and fascists there are *socialists*. The liberals stop being a majority: they are still the biggest group, but voting together is no longer enough for them.
Every player has a *role* (which never changes) and a *party membership* (which can change). *You win with your party membership, not with your role*, unless you are Hitler: Hitler always wins with the fascists.
Who knows what:
- The fascists know each other and know who Hitler is.
- *Hitler knows nobody*, not even in small games (in the classic game, with 5 or 6 players, he did know his fascist).
- The socialists know each other.
- The liberals, as always, know nothing.
If you want to ask for a role before the game starts, */role* also offers you *Socialist* (and the combinations with the other roles). It is a request, not a guarantee: if someone else already took the slot, you get something else.

*HOW YOU WIN*
- *Liberals*: by enacting their liberal policies (5, or *6 in 8-player games*) or by killing Hitler.
- *Fascists*: by enacting 6 fascist policies, or by getting Hitler elected chancellor in the Hitler Zone.
- *Socialists*: by completing their whole socialist track (5 policies with 6-8 players, 6 policies from 9 up).
The socialists *lose in every ending that involves Hitler*: if they elect him chancellor the fascists win, and if they kill him the liberals win.

*THE DECK*
5 liberal policies, 10 fascist and 8 socialist. In 8-player games one fascist is removed and one liberal is added (6/9/8).
The *fascist track is different from all the classic ones* and is always the same no matter how many of you there are: empty, investigate loyalty, policy peek, execution, execution (the veto unlocks here) and fascist victory.""",
    'explain.socialista_2': """*CHAIRMAN* \U0001F3DB
This is a third government office that does not exist in the classic game. After the government wins the vote, the *chancellor picks a Chairman* (anyone except themselves and the president), and that person *privately peeks at the top policy of the deck* before the president draws the three.
It lasts a single round and *does not make you term-limited*: the Chairman can be nominated chancellor the next round, unlike the outgoing president and chancellor.

*THE SOCIALIST POWERS*
When a socialist policy is enacted, the power belongs to *the socialist party*, not to the president. Two consequences:
- They are used the same way if the policy came out *through anarchy* (presidential powers, by contrast, are lost).
- The decisions belong to *the whole party*: any socialist proposes someone and the power is only applied if *all* the other living socialists agree. If anyone says no, the proposal is dropped and you pick again. With a single living socialist there is nobody to ask, so it applies straight away.

\U0001F41B *Illegal Bug*: they see a player's party membership.
\u270A *Recruitment*: they convert a player, who then has socialist party membership and wins with them. They keep their role and everything they already knew.
5\uFE0F\u20E3 *Five-Year Plan*: 2 socialist policies and 1 liberal one are added to the deck, and it is shuffled.
\U0001F3DB *Congress*: the recruited player finds out who the original socialists were.
\U0001F4D6 *Confession*: the president shows their party membership to whoever the socialists pick. The group is told who saw it.

The Bug, the Recruitment and the Congress are *secret actions*: the group finds out the power was used, but not on whom. The Five-Year Plan and the Confession are public. Everything secret is revealed in the hidden history when the game ends.

*Careful: not every socialist track has the same powers.* With 6-8 players there is no Confession; with 11 or more there is no Bug and no Congress, the first slot gives nothing and there are *two* Recruitments. Look at your track with */board*.

*IF THEY RECRUIT HITLER*
Hitler's card is swapped like anyone else's, so *whoever investigates him (or bugs him, or receives his Confession) will see socialist*. But for everything else he is still a fascist: he takes no part in the socialist decisions, he does not wake up for the Congress and he *wins with the fascists*.
The socialists *do not find out at the time* that it failed; they only discover it at the Congress, when no new socialist shows up. Hitler does know what happened, and knows he now looks like a socialist.

*CENSORSHIP* \U0001F576
When the *third socialist policy* is enacted, Censorship kicks in. It works like the Hitler Zone: it lasts for the rest of the game and *removes the Chairman*. From then on the chancellor no longer picks anyone and the policies are drawn directly.

*WHAT DOES NOT CHANGE*
Nomination, voting, the election tracker, anarchy, the Hitler Zone (3 fascist policies), the veto with the fifth fascist policy, the presidential powers and the usual commands (/board, /mvp, /info, etc.).

*/GUESS*
Since nobody knows the socialists at the start (except themselves), they are added to the guess: liberals guess fascists, Hitler *and original socialists*; Hitler guesses his teammates *and the original socialists*; and the fascists, who already know each other, guess *only the original socialists*. Recruited players do not count: everyone plays the /guess of their original role. The socialists guess fascists and Hitler, like a liberal in the classic game.
With */board* you see the three tracks and with */symbols* what each symbol means. If you were recruited, */info* tells you so.""",
    'fix.chancellor_announce': '*{}* was nominated as chancellor. Please vote now!',
    'fix.president_choose_discard': 'Cards fixed. Please choose which one to discard:',
    'guessresults.choose_game': 'Choose the game to see the guess results',
    'guessresults.nobody_guessed': 'Nobody used /guess in that game.',
    'history.group_header': 'History of the group *{}*:\n\n',
    'history.mode.compacto': 'compact',
    'history.mode.extendido': 'extended',
    'history.mode_arg.compacto': 'compact',
    'history.mode_arg.extendido': 'extended',
    'history.mode_footer': '_History mode: {}. To change it: /history {}_',
    'history.mode_saved': '{}: your history mode is now {}. It will be used in all your games.',
    'history.mode_save_failed': 'I could not save your history mode, please try again later.',
    'history.mode_unknown': 'Unknown mode. Use /history compact or /history extended.',
    'info.choose_game': 'Choose the game to get /info in private',
    'info.group_header': '--- *Info for the group {}* ---\n',
    'info.must_be_player': 'You have to be a player in the game to get information.',
    'info.no_game_here': 'There is no game created in this chat',
    'join.already_joined': 'You already joined the game, %s!',
    'join.already_started': 'The game has already started. Please wait for the next one!',
    'join.dm_welcome': 'You joined a game in %s. I will tell you your secret role soon.',
    'join.joined_enough': ' joined the game. Type /startgame if this is the last player and you want to start with %d players!',
    'join.joined_many': '%s joined the game. There are %d players in the game and %d-%d players are needed',
    'join.joined_one': '%s joined the game. There is %d player in the game and %d-%d players are needed.',
    'join.max_players': 'You have reached the maximum number of players. Please start the game with /startgame!',
    'join.no_private_chat': ', I cannot send you a private message. Please go to @secrethitlertestlbot and hit "Start".\nThen you need to type /join again.',
    'leave.already_started': '\u203C\u203C*The game already started and the admin does not allow leaving games*\u203C\u203C',
    'leave.no_game': '\u203C\u203C*There is no game to leave*\u203C\u203C',
    'leave.success': '\u203C\u203C*You have left the game*\u203C\u203C',
    'miguess.choose_game': 'Choose the game to see your own /guess result',
    'miguess.you_didnt_guess': 'You did not use /guess in that game.',
    'nextgame.dm_ack': '\U0001F3B2 Done! I will ping you here as soon as a new game is created in %s.',
    'nextgame.no_private_chat': ', I cannot send you a private message. Please go to @secrethitlertestlbot and hit "Start" so I can reach you.',
    'nextgame.notify': '\U0001F3B2 A new game was created in %s! Join with /join.',
    'nextgame.registered': '%s wants to play the next game. I will ping them privately as soon as one is created with /newgame.',
    'prueba.already_ended': 'The game is already over, you can no longer change whether it counts or is a test. You can mark the next one with /prueba.',
    'prueba.only_player': 'Only a player in the game can mark it as a test game.',
    'reload.nothing_to_reload': 'There is no game to reload! Create a new one with /newgame!',
    'reload.vote_in_progress': 'There is a vote in progress, use /calltovote to tell the other players. ',
    'retract.announce': '%s has withdrawn their vote.',
    'retract.choose_group': 'Choose the group you want to withdraw your vote from',
    'retract.done_group': 'You withdrew your vote in the group *{}*. You can vote again here.\nDo you want to elect President *{}* and chancellor *{}*?',
    'retract.no_active_vote': 'You have no active vote to withdraw.',
    'retract.no_active_vote_there': 'You have no active vote to withdraw in that group.',
    'retract.nothing_to_retract': 'You have not voted yet, there is no vote to withdraw!',
    'retract.vote_closed': 'The vote is no longer active, there is no vote to withdraw.',
    'roles.col_fascista': 'Fas',
    'roles.col_ganar': 'Win',
    'roles.col_hitler': 'Hit',
    'roles.col_jugadores': 'Ply',
    'roles.col_liberal': 'Lib',
    'roles.col_mazo': 'Deck',
    'roles.col_socialista': 'Soc',
    'roles.legend': '*Deck* = liberal/fascist(/socialist) policies the deck starts with.\n*Win* = policies each track needs to win, in the same order.',
    'roles.other_mode_clasico': 'Use */roles classic* to see the classic table.',
    'roles.other_mode_socialista': 'Use */roles socialist* to see the Socialist Expansion table.',
    'roles.title_clasico': '\U0001F465 *Roles and deck by player count* (classic mode)',
    'roles.title_socialista': '\U0001F465 *Roles and deck by player count* (Socialist Expansion)',
    'roles.unknown_mode': 'I do not know that mode. Use /roles, /roles classic or /roles socialist.',
    'role.ask': 'Which role would you like to be?',
    'role.ask_socialist': 'Which role would you like to be? (game with the Socialist Expansion)',
    'role.chosen': 'Message edited: you chose the role: %s',
    'role.game_started': 'The game already started, try again when a game has not started yet',
    'role.no_game': 'There is no game created, try again once a game exists',
    'role.not_joined': 'You have not joined this game, try again once you have joined',
    'rules.text': """On each turn the active player, the *President* from now on, picks a player as their *chancellor*.
\tThen every player votes on whether they accept the proposed government.
\tIf there is a majority of *JA!* votes (yes), the government takes office.
\tIn that case the *president* receives 3 cards from the policy deck, which initially holds
\t*11 fascist policies*
\t*6 liberal policies*
\tOn receiving the cards the president gets a private keyboard with the 3 cards and is asked to
\t*DISCARD* one of them and pass the other two to the chancellor.
\tThe chancellor receives the two remaining policies and picks one to enact.

\tThe fascists' goal is to enact *6 fascist policies* or *3 of them and get Hitler elected chancellor*.
\tThe liberals' goal is to enact *5 liberal policies* or *kill Hitler*.

\tWhen a fascist policy is enacted there may be an action for the *president* attached to it.
\t/symbols gives a summary of what each action does.
\t""",
    'start.already_started': 'The game has already started!',
    'start.description': '"Secret Hitler is a social deduction game for 5-10 players about finding Hitler and stopping the rise of fascism. Most players are liberals. If they can learn to trust each other, they have enough votes to control the parliament and win the game. But some players are fascists. They will say whatever it takes to get elected, promote fascism and blame everybody else for the fall of the Republic. The liberals have to work together to find the truth before the fascists install their heartless leader and win the game." From the official Secret Hitler description. Add me to a group and type /newgame to create a game!',
    'start.not_enough_players': 'There are not enough players (min. %d, max. %d). Join the game with /join',
    'start.only_creator': 'Only the game creator or a group admin can start the game with /startgame',
    'stats.as_fascist': 'Games as Fascist:  *{1}/{0}* Won: *{2}/{1}*\n',
    'stats.as_hitler': 'Games as Hitler:  *{1}/{0}* Won: *{2}/{1}*\n',
    'stats.as_liberal': 'Games as liberal: *{1}/{0}* Won: *{2}/{1}*\n',
    'stats.best_teammates': 'Won the most games with: *{0}* ({1} times)\n',
    'stats.cancelled_games': 'Cancelled games: *',
    'stats.fas_hitler_chancellor': 'Fascist wins (Hitler Chanc): *',
    'stats.fas_policies': 'Fascist wins (Policies): *',
    'stats.games_died': 'Games where they died:  *{1}/{0}*\n',
    'stats.games_played': 'Games played: *{0}*\n',
    'stats.games_won': 'Games won:  *{1}/{0}* {2:.2f}%\n',
    'stats.header': '+++ Stats +++\n',
    'stats.lib_hitler': 'Liberal wins (Hitler \u2620): *',
    'stats.lib_policies': 'Liberal wins (Policies): *',
    'stats.most_killed': 'Killed the most: *{0}* ({1} times)\n',
    'stats.most_killed_by': 'Killed by the most: *{0}* ({1} times)\n',
    'stats.multiple_players': "There is more than one player named '{0}':",
    'stats.no_new_stats': 'There are no new stats yet for {0}. Ask an admin to use /vincularstats to link the old games, or keep playing to generate new stats.',
    'stats.no_stats_for_name': "There are no new stats for anyone named '{0}'.",
    'stats.people_killed': '\nPeople they killed: *{0}*\n',
    'stats.player_header': '+++ Stats for *{0}* +++\n',
    'stats.query_empty': 'The query returned nothing',
    'stats.query_result': 'Query result:',
    'stats.soc_policies': 'Socialist wins (Policies): *',
    'stats.that_id': 'ID {0}',
    'stats.total_games': 'Total games: *',
    'stats.updated': 'Stats updated',
    'stats.use_logros_id': '\nUse /logros <ID> to see the achievements of a specific one.',
    'stats.use_stats2_id': '\nUse /stats2 <ID> to see the stats of a specific one.',
    'stats.user_has_no_stats': 'This user has no stats',
    'stats.worst_teammates': 'Lost the most games with: *{0}* ({1} times)\n',
    'stats.you': 'you',
    'vote.not_started': 'The vote has not started yet!',
    'votes.has_not_voted': '%s has *not* voted.\n',
    'votes.has_voted': '%s has voted.\n',
    'votes.history_header': 'Voting history for President %s and Chancellor %s:\n\n',
    'votes.wait_five_minutes': 'Five minutes have to go by before you can see the votes',
})

# --- /guess, /miguess and /mvp -----------------------------------------------------
TEXTS.update({
    'guess.already_picked': 'You already picked: {}\n',
    'guess.already_twice': 'You already guessed twice. Your second pick is *final* and cannot be changed again.',
    'guess.btn_confirm': '✅ Confirm',
    'guess.btn_dont_know': '\U0001F937 No idea',
    'guess.btn_restart': '↩️ Start over',
    'guess.cannot_guess': 'You cannot guess in this game.',
    'guess.changed_once': ' _(changed their guess once)_',
    'guess.choose_game': 'Choose the game to guess who is a fascist and who is Hitler',
    'guess.closest_to_truth': '\n\U0001F3C6 Closest to the truth: *{}* ({} out of {} pts)',
    'guess.confirm_full': '\U0001F52E *Confirm your guess*\nSuspected fascists: {}\nHitler: {}\n\nConfirm?',
    'guess.confirm_hitler': '\U0001F52E *Confirm your guess*\nSuspected fascist teammates: {}\n\nConfirm?',
    'guess.confirm_prediction': '\U0001F52E *Confirm your prediction*\nWho will guess Hitler and the fascists best?: *{}*\n\nConfirm?',
    'guess.date_note': ' _({})_',
    'guess.dont_know_short': 'no idea',
    'guess.fascist_no_prediction': '*{}* (fascist) did not risk a guess on who would do best at finding Hitler and the fascists \U0001F937{}',
    'guess.fascist_predicted': '*{}* (fascist) predicted that *{}* would do best at finding Hitler and the fascists{}',
    'guess.game_inactive': 'That game is no longer active.',
    'guess.hit': 'got it right ✅',
    'guess.hitler_line': '*{}* (Hitler) {}{}\n   ↳ Got {}/{} teammates right',
    'guess.hitler_no_guess': 'did not risk a guess on who their fascist teammates were \U0001F937',
    'guess.hitler_suspected': 'suspected their fascist teammates were: {}',
    'guess.intro_fascist': '\U0001F52E You are a *fascist*, so instead of guessing roles you are going to predict who you think will do best at finding Hitler and the regular fascists. If you have no idea yet you can tap "\U0001F937 No idea" and leave it blank. You can redo this pick one more time after confirming; both attempts are saved, but the *second* one is the final one.',
    'guess.intro_hitler': '\U0001F52E You are *Hitler*, so instead of guessing who Hitler is you are going to try to identify your fascist teammates. If you have no idea about one of them you can tap "\U0001F937 No idea" and leave it blank. You can redo this pick one more time after confirming; both attempts are saved, but the *second* one is the final one.',
    'guess.intro_liberal': '\U0001F52E You are going to pick who you think the regular fascists are and who Hitler is. You do not have to fill it all in: tap "\U0001F937 No idea" for whatever you have no clue about and leave it blank. You can redo this pick one more time after confirming; both attempts are saved, but the *second* one is the final one.',
    'guess.last_chance': '\U0001F52E This is your *last* chance to guess: whatever you confirm now is final.',
    'guess.liberal_line': '*{}* {} and {}{}\n   ↳ Got {}/{} regular fascists right, {} on Hitler ({} pts)',
    'guess.miss': 'got it wrong ❌',
    'guess.must_be_player': 'You have to be a player in the game to use /guess.',
    'guess.must_be_player_guess': 'You have to be a player in the game to guess.',
    'guess.my_reveal_title': '\U0001F52E *Your guess result* \U0001F52E\n',
    'guess.no_fascist_guess': 'did not risk a guess on who the fascists were \U0001F937',
    'guess.no_hitler_guess': 'did not risk a guess on who Hitler was \U0001F937',
    'guess.no_risk': 'did not risk it \U0001F937',
    'guess.no_risk_cap': 'Did not risk it \U0001F937',
    'guess.pick_another': 'Pick another suspect (or "No idea" to leave the rest blank):',
    'guess.pick_header': '\U0001F52E *Guess who {} are* ({}/{})\n',
    'guess.predicted_right': 'Predicted correctly ✅',
    'guess.predicted_wrong': 'Got it wrong ❌',
    'guess.prediction_question': '\U0001F52E *Who do you think will do best at finding Hitler and the regular fascists?*',
    'guess.reveal_title': '\U0001F52E *Guess results* \U0001F52E\n',
    'guess.said_hitler_was': 'said Hitler was *{}*',
    'guess.saved': '✅ Done! Your guess is saved (recorded on {}). You can use /guess one more time to change it (the second one is final). Who got closest to the truth is revealed at the end of the game.',
    'guess.saved_final': '✅ Done! That was your second time, so your guess is *final* and cannot be changed. It was recorded on {}. Who got closest to the truth is revealed at the end of the game.',
    'guess.sent_dm': 'I sent you a private message so you can make your guess. Check your private chat with me!',
    'guess.session_expired': 'Your /guess session expired, use /guess again to start over.',
    'guess.suspected': 'suspected: {}',
    'guess.title_fascists': 'the regular fascists',
    'guess.title_hitler_teammates': 'your fascist teammates',
    'guess.who_is_hitler': '\U0001F52E *Who do you think is Hitler?*',
    'guess.confirm_full_soc': '\U0001F52E *Confirm your guess*\nSuspected fascists: {}\nHitler: {}\nSuspected original socialists: {}\n\nConfirm?',
    'guess.confirm_hitler_soc': '\U0001F52E *Confirm your guess*\nSuspected fascist teammates: {}\nSuspected original socialists: {}\n\nConfirm?',
    'guess.confirm_socialists': '\U0001F52E *Confirm your guess*\nSuspected original socialists: {}\n\nConfirm?',
    'guess.fascist_socialists_line': '*{}* (fascist){}',
    'guess.intro_fascist_soc': '\U0001F52E You are a *fascist*: you already know your teammates and Hitler, but not who the *original socialists* are (those who started the game as socialists: recruited players do not count), so your guess is to find them. If you have no idea about one of them you can tap "\U0001F937 No idea" and leave it blank. You can redo this pick one more time after confirming; both attempts are saved, but the *second* one is the final one.',
    'guess.intro_hitler_soc': '\U0001F52E You are *Hitler* and you know nobody, so you are going to try to identify your fascist teammates and also the *original socialists* (those who started the game as socialists: recruited players do not count). Tap "\U0001F937 No idea" for whatever you have no clue about and leave it blank. You can redo this pick one more time after confirming; both attempts are saved, but the *second* one is the final one.',
    'guess.intro_liberal_soc': '\U0001F52E You are going to pick who you think the regular fascists are, who Hitler is and who the *original socialists* are (those who started the game as socialists: recruited players do not count). You do not have to fill it all in: tap "\U0001F937 No idea" for whatever you have no clue about and leave it blank. You can redo this pick one more time after confirming; both attempts are saved, but the *second* one is the final one.',
    'guess.no_socialist_guess': 'did not risk a guess on who the original socialists were \U0001F937',
    'guess.socialists_result': '{} — got {}/{} original socialists right',
    'guess.socialists_suspected': 'suspected the original socialists were: {}',
    'guess.title_socialists': 'the original socialists',
    'mvp.ask': '\U0001F3C5 *Who was the MVP of the game?*\n(You cannot vote for yourself)',
    'mvp.can_change': ' You can change your vote at any time with /mvp while votes are still missing.',
    'mvp.choose_game': 'Choose the game where you want to vote for the MVP',
    'mvp.co_mvps': '\n\U0001F3C6 The MVPs of the game are {}!',
    'mvp.current_vote': '\n\nYou are currently voting for: *{}*. You can change it by picking another player while votes are still missing.',
    'mvp.everyone_voted': 'Everybody voted! The MVP result is revealed shortly.',
    'mvp.missing_line': '[%s](tg://user?id=%d) - use /mvp in private!\n',
    'mvp.must_be_player': 'You have to be a player in the game to use /mvp.',
    'mvp.must_be_player_vote': 'You have to be a player in the game to vote.',
    'mvp.no_other_players': 'There are no other players to vote for in this game.',
    'mvp.no_recent_games': 'You have no recently finished games where you can vote for the MVP.',
    'mvp.no_self_vote': 'You cannot vote for yourself as MVP.',
    'mvp.no_votes': '\U0001F3C5 The MVP vote closed with no votes. There is no MVP this game.',
    'mvp.not_ended': 'The game is not over yet. Wait until it ends to vote for the MVP.',
    'mvp.not_voted_yet': '\n\nStill to vote: {}',
    'mvp.player_gone': 'That player is no longer in the game.',
    'mvp.reveal_title': '\U0001F3C5 *MVP vote of the game* \U0001F3C5\n',
    'mvp.sent_dm': 'I sent you a private message so you can vote for the MVP. Check your private chat with me!',
    'mvp.still_missing_header': '\U0001F3C5 These players still have to vote for the MVP of the game:\n',
    'mvp.tally_plural': '{}: {} votes',
    'mvp.tally_singular': '{}: {} vote',
    'mvp.the_mvp': '\n\U0001F3C6 The MVP of the game is *{}*!',
    'mvp.tie': '\n\U0001F91D The vote was tied, there is no MVP this game.',
    'mvp.voted': '✅ Done! You voted for *{}* as MVP of the game.{}',
    'myguess.attempt': 'Attempt {}',
    'myguess.fascist_line': '*{}*{}: you predicted that *{}* would do best at finding Hitler and the fascists',
    'myguess.fascist_none': '*{}*{}: you did not risk a guess on who would do best at finding Hitler and the fascists \U0001F937',
    'myguess.final': ' (final)',
    'myguess.hitler_line': '*{}*{}: you suspected {} were your fascist teammates',
    'myguess.hitler_none': '*{}*{}: you did not risk a guess on who your fascist teammates were \U0001F937',
    'myguess.line': '*{}*{}: {} and {}',
    'myguess.no_fascists': 'you did not risk a guess on who the fascists were \U0001F937',
    'myguess.no_hitler': 'you did not risk a guess on who Hitler was \U0001F937',
    'myguess.said_hitler': 'you said Hitler was *{}*',
    'myguess.suspected': 'you suspected {}',
    'myguess.title': '\U0001F52E *Your /guess picks*',
    'myguess.fascist_socialists': '*{}*{}:',
    'myguess.no_socialists': 'you did not risk a guess on who the original socialists were \U0001F937',
    'myguess.socialists': 'you suspected the original socialists were {}',
})

# --- Achievement names and descriptions (Constants/Achievements) -------------------
TEXTS.update({
    'logro.actor_completo.name': 'Complete actor',
    'logro.actor_completo.desc': 'You won at least once as Liberal, Fascist and Hitler.',
    'logro.alma_en_pena.name': 'Lost soul',
    'logro.alma_en_pena.desc': 'You were executed 10 times in total.',
    'logro.bala_certera.name': 'Straight shot',
    'logro.bala_certera.desc': 'You executed Hitler and the liberals won.',
    'logro.camarada_de_hierro.name': 'Comrade of steel',
    'logro.camarada_de_hierro.desc': 'You played {cantidad} games as a Socialist.',
    'logro.carne_de_canon.name': 'Cannon fodder',
    'logro.carne_de_canon.desc': 'You were executed 5 times in total.',
    'logro.cazador_de_hitler.name': 'Hitler hunter',
    'logro.cazador_de_hitler.desc': 'You executed Hitler in 2 different games.',
    'logro.companeros_de_ideologia.name': 'Fellow travellers',
    'logro.companeros_de_ideologia.desc': 'As Hitler, you correctly identified all of your fascist teammates with /guess.',
    'logro.companeros_de_ideologia_precoz.name': 'Instant complicity',
    'logro.companeros_de_ideologia_precoz.desc': 'As Hitler, you identified all of your fascist teammates with /guess before the 8th presidency.',
    'logro.converso_ganador.name': 'Convert militant',
    'logro.converso_ganador.desc': 'The socialists recruited you and you won with them.',
    'logro.democracia_impecable.name': 'Flawless democracy',
    'logro.democracia_impecable.desc': 'You won as a liberal with 5 liberal policies and nobody executed.',
    'logro.detective.name': 'Detective',
    'logro.detective.desc': 'You correctly guessed every fascist and Hitler with /guess.',
    'logro.detective_precoz.name': 'Early detective',
    'logro.detective_precoz.desc': 'You correctly guessed every fascist and Hitler with /guess before the 8th presidency.',
    'logro.dude_de_los_mios.name': 'I doubted my own',
    'logro.dude_de_los_mios.desc': 'As Hitler, your first /guess got all your fascist teammates right, but your second one got them wrong.',
    'logro.en_racha.name': 'On a roll',
    'logro.en_racha.desc': 'You won 3 games in a row.',
    'logro.error_de_calculo.name': 'Miscalculation',
    'logro.error_de_calculo.desc': 'As a liberal, you executed another liberal.',
    'logro.gafe.name': 'Jinxed',
    'logro.gafe.desc': 'You were executed 3 times in total.',
    'logro.hitler_ganador.name': 'Supreme Chancellor',
    'logro.hitler_ganador.desc': 'You won a game as Hitler.',
    'logro.hitler_incognito.name': 'Hidden in plain sight',
    'logro.hitler_incognito.desc': 'You won as Hitler without ever being investigated.',
    'logro.hitler_reclutado_ganador.name': 'Mole in the revolution',
    'logro.hitler_reclutado_ganador.desc': 'As Hitler the socialists recruited you and you still won with the fascists.',
    'logro.ideologo_completo.name': 'Complete ideologue',
    'logro.ideologo_completo.desc': 'You won at least once as Liberal, Fascist, Hitler and Socialist.',
    'logro.imparable.name': 'Unstoppable',
    'logro.imparable.desc': 'You won 5 games in a row.',
    'logro.intocable.name': 'Untouchable',
    'logro.intocable.desc': 'You played 10 games without ever being executed.',
    'logro.jugo_socialista.name': 'There is a third party',
    'logro.jugo_socialista.desc': 'You played a game with the Socialist Expansion.',
    'logro.leyenda.name': 'Legend',
    'logro.leyenda.desc': 'You played 100 games.',
    'logro.lo_sabia.name': 'I knew it!',
    'logro.lo_sabia.desc': 'You correctly guessed who Hitler was with /guess.',
    'logro.martir.name': 'Martyr of the Republic',
    'logro.martir.desc': 'You were executed as a liberal and your team won anyway.',
    'logro.martir_fascista.name': 'Fallen for the cause',
    'logro.martir_fascista.desc': 'You were executed as a fascist and your team won anyway.',
    'logro.mas_muerto_que_alee.name': 'Deader than Alee',
    'logro.mas_muerto_que_alee.desc': 'You were executed more than 10 times in total.',
    'logro.me_toco_lo_que_pedi.name': 'I got what I asked for',
    'logro.me_toco_lo_que_pedi.desc': 'You got the role you asked for and you won.',
    'logro.mision_imposible.name': 'Mission Impossible',
    'logro.mision_imposible.desc': 'You won a game on the same team as a very particular player.',
    'logro.mvp_cinco_veces.name': 'Recurring MVP',
    'logro.mvp_cinco_veces.desc': 'You were voted MVP in 5 games.',
    'logro.mvp_mas_de_diez.name': 'The usual MVP',
    'logro.mvp_mas_de_diez.desc': 'You were voted MVP in more than 10 games.',
    'logro.mvp_una_vez.name': 'MVP',
    'logro.mvp_una_vez.desc': 'You were voted MVP of the game.',
    'logro.no_debi_dudar.name': 'I should not have doubted',
    'logro.no_debi_dudar.desc': 'Your first /guess got Hitler right, but your second one got it wrong.',
    'logro.piloto_automatico.name': 'Autopilot',
    'logro.piloto_automatico.desc': 'You won a game with the automatic Ja vote turned on.',
    'logro.prediccion_certera.name': 'Fascist eye',
    'logro.prediccion_certera.desc': 'As a fascist, you correctly predicted who would guess best with /guess.',
    'logro.prediccion_certera_precoz.name': 'Fascist seer',
    'logro.prediccion_certera_precoz.desc': 'As a fascist, you correctly predicted who would guess best with /guess before the 8th presidency.',
    'logro.premio_consuelo.name': 'Consolation prize',
    'logro.premio_consuelo.desc': 'You lost 5 games in a row.',
    'logro.primera_partida.name': 'First time',
    'logro.primera_partida.desc': 'You played your first game.',
    'logro.purga_roja.name': 'Purge',
    'logro.purga_roja.desc': 'You executed a Socialist.',
    'logro.reclutamos_a_hitler.name': 'Comrade Hitler',
    'logro.reclutamos_a_hitler.desc': 'The socialists burned their Recruitment on Hitler.',
    'logro.regimen_consolidado.name': 'Consolidated regime',
    'logro.regimen_consolidado.desc': 'You won as a fascist by enacting 6 fascist policies.',
    'logro.revolucion_pura.name': 'Pure revolution',
    'logro.revolucion_pura.desc': 'You won with the socialists without recruiting anyone.',
    'logro.socialista_ganador.name': 'Triumphant revolution',
    'logro.socialista_ganador.desc': 'You won a game with the socialists.',
    'logro.socialista_martir.name': 'Martyr of the revolution',
    'logro.socialista_martir.desc': 'You were executed while on the socialist team and your team won anyway.',
    'logro.tres_frentes.name': 'Three fronts',
    'logro.tres_frentes.desc': 'You won a socialist-mode game without being on the socialist team.',
    'logro.verdugo.name': 'Executioner',
    'logro.verdugo.desc': 'You executed 3 players in total.',
    'logro.veterano.name': 'Veteran',
    'logro.veterano.desc': 'You played 25 games.',
})

# --- Texts that do not come straight from a literal in the code --------------------
TEXTS.update({
    # Game names as they are shown (the values stored in the game state stay Spanish)
    'common.or': 'or',
    'role.liberal': 'Liberal',
    'role.fascista': 'Fascist',
    'role.hitler': 'Hitler',
    'role.socialista': 'Socialist',
    'party.liberal': 'liberal',
    'party.fascista': 'fascist',
    'party.socialista': 'socialist',
    'policy.liberal': 'liberal',
    'policy.fascista': 'fascist',
    'policy.socialista': 'socialist',

    # Role list at the end of the game (Game.print_roles)
    'roles.line': "{nombre}'s {muerto}role was {rol}{reclutado} {preferencia}",
    'roles.dead_mark': '(dead) ',
    'roles.recruited_mark': ' (recruited by the socialists)',
    'roles.wanted': 'wanted to be {preferencia}',

    # Board (/board)
    'board.liberal_track': '--- Liberal Policies ---',
    'board.fascist_track': '--- Fascist Policies ---',
    'board.socialist_track': '--- Socialist Policies ---',
    'board.election_tracker': '--- Election Tracker ---',
    'board.president_order': '--- Presidential Order  ---',
    'board.policies_left': 'There are {cantidad} policies left in the policy deck.',
    'board.hitler_zone_warning': '‼️ Careful: if Hitler is elected Chancellor the fascists win the game! ‼️',
    'board.censorship_active': '\U0001F576 Censorship is active: no more Chairman.',
    'board.not_hitlers': 'We know the following players are not Hitler, because they were elected Chancellor after 3 fascist policies:',

    # Private player info (/info)
    'info.header': '--- *Info for player {nombre}* ---',
    'info.role_and_party': 'You are *{rol}* and your party membership is *{afiliacion}*',
    'info.autoja_on': 'Automatic Ja vote (/startautoja): *On*, it stops {corte}',
    'info.autoja_off': 'Automatic Ja vote (/startautoja): *Off*',
    'info.fascist_teammates': 'Your fascist teammates are: *{nombres}*',
    'info.hitler_is': 'Hitler is: *{nombre}*',
    'info.your_fascist_partner': 'Your fascist partner is: *{nombre}*',
    'info.only_socialist': 'You are the only socialist of origin in this game.',
    'info.socialist_teammates': 'Your socialist teammates are: *{nombres}*',
    'info.recruited_hitler': ('✊ The socialists *recruited* you, but you are Hitler: it does not work on you. '
                             'You still win with the fascists and you take no part in their decisions. '
                             'That said, you now hold the socialist card, so anyone who investigates you will see *socialist*.'),
    'info.recruited': '✊ You were *recruited by the socialists*: you now win with them.',

    # When the automatic Ja vote stops (/startautoja)
    'autoja.corte.ambas': 'when there are 3 fascist policies (Hitler Zone) *or* {cantidad} policies enacted in total',
    'autoja.corte.fascistas': 'only when there are 3 fascist policies (Hitler Zone)',
    'autoja.corte.politicas': 'only when there are {cantidad} policies enacted in total',
    'autoja.btn.ambas': 'Both (recommended)',
    'autoja.btn.fascistas': 'Only 3 fascists',
    'autoja.btn.politicas': 'Only {cantidad} policies',

    # /help and /symbols
    'help.header': 'The following commands are available:',
    'help.commands': """/help - Gives you information about the available commands
/start - Gives you some information about Secret Hitler
/symbols - Shows you every symbol that can appear on the board
/rules - Gives you a link to the official site with the Secret Hitler rules
/roles - Shows how many liberals, fascists, socialists and policies there are per player count (/roles socialist for the expansion)\n/language - Changes the bot language in this group (Spanish or English)
/newgame - Creates a new game or loads a previous one
/newgame socialista - Creates a game with the Socialist Expansion: a third party, with its own track and its own powers (6 to 13 players)
/explainsocialista - Explains how the socialist mode is played and how it differs from the classic one
/nextgame - Notes that you want to play the next game and pings you privately when one is created with /newgame
/join - Joins you to an existing game. If used as a reply to another player's message, joins that player instead
/startgame - Starts an existing game once every player has joined
/cancelgame - Cancels an existing game, all of its data is deleted.
/board - Prints the current board with the liberal and fascist tracks, presidential order and election tracker
/history - Prints the history of the current game. /history extended shows each player's vote, one per line, and /history compact summarizes it again; your choice is saved for your future games
/votes - Prints who has voted
/calltovote - Tells the players it is time to vote (or who still has to vote for the MVP if the game already ended)
/retirar - Withdraws your Ja or Nein vote so you can vote again
/startautoja - Turns on your automatic Ja vote as soon as a government is proposed, and lets you choose when it stops: at 3 fascist policies, at 5 enacted policies, or at either of them
/stopautoja - Turns off your automatic Ja vote
/conflicto - Turns off the automatic Ja vote for every player in the game
/logros - Shows your unlocked achievements
/guess - Privately guess who the fascists and Hitler are
/mvp - Privately vote for the best player of the game
/prueba - Marks the game as a test game (it does not count for stats, achievements or MVP) or makes it count again
/end - Closes the MVP vote without waiting for everybody to vote
/guessresults - Reprints the guess results of the game that just ended
/miguess - Privately shows only your own /guess result
/version - Shows the current bot version
/all - Mentions every known member of the group""",
    'symbols.header': 'The following symbols appear on the board:',
    'symbols.list': (
        '◻️ Empty slot with no special power\n'
        '✖️ Slot covered by a card\n'
        '\U0001F52E Presidential Power: Policy Peek\n'
        '\U0001F50E Presidential Power: Investigate Loyalty\n'
        '\U0001F5E1 Presidential Power: Execution\n'
        '\U0001F454 Presidential Power: Call Special Election\n'
        '\U0001F54A Liberals win\n'
        '☠ Fascists win\n'
        '\U0001F41B Socialist Power: Illegal Bug (the socialists see a party membership)\n'
        '✊ Socialist Power: Recruitment (they convert a player)\n'
        '5️⃣ Socialist Power: Five-Year Plan (2 socialist policies and 1 liberal into the deck)\n'
        '\U0001F3DB Socialist Power: Congress (the new socialists meet the original ones)\n'
        '\U0001F4D6 Socialist Power: Confession (someone sees the President\'s party membership)\n'
        '☭ Socialists win'),

    # /prueba
    'prueba.on': ('\U0001F9EA This is a *test game*: when it ends no stats will be saved, no '
                  'achievements are granted and there is no MVP vote.\n'
                  'Use /prueba again if you want the game to count.'),
    'prueba.off': ('✅ This game *counts*: when it ends the stats are saved, the achievements '
                   'are granted and the MVP is voted.\n'
                   'Use /prueba again if you want it to be just a test.'),
    'prueba.board_reminder': '\U0001F9EA *Test game* (does not count for stats, achievements or MVP)',

    # /language
    'lang.current': 'Current language of this chat: *{idioma}*.',
    'lang.ask': 'Which language do you want to play in?',
    'lang.changed': ('\U0001F310 Done, from now on this chat plays in *{idioma}*.\n'
                     'It applies to the whole group and to the private messages of its games.'),
    'lang.unknown': "I don't know that language. Use /language with one of these: {opciones}",
    'lang.save_failed': 'I could not save the language, try again in a bit.',

    # /stad
    'stad.params': 'Population: {}\nSuccesses in population: {}\nCards drawn: {}\nSuccesses: {}',
    'stad.result': 'Exactly:        {}%\nAt least:       {}%',

    # Achievements: category titles and listing texts
    'logro.cat.roles': 'Roles and victories',
    'logro.cat.socialista': 'Socialist Expansion',
    'logro.cat.muerte': 'Death and executions',
    'logro.cat.hitos': 'Milestones',
    'logro.cat.social': 'Social',
    'logro.unlocked_title': '\U0001F3C6 *New achievements!*\n\n',
    'logro.unlocked_line': '%s unlocked %s *%s*',
    'logro.and_more': '\n...and %d more achievements (/logros)',
    'logro.and_more_one': '\n...and %d more achievement (/logros)',
    'logro.see_all': '\n\nSee all of yours with /logros',
    'logro.list_title': '\U0001F3C6 *Achievements of %s* (%d/%d)\n',
    'logro.secret': 'Secret achievement',

    # Telegram "/" menu
    'menu.help': 'Information about the available commands',
    'menu.start': 'Gives some information about Secret Hitler',
    'menu.rules': 'Link to the official site with the rules',
    'menu.explainsocialista': 'Explains the socialist mode and its differences',
    'menu.symbols': 'Shows the symbols that can appear on the board',
    'menu.language': 'Changes the bot language in this group',
    'menu.newgame': 'Creates a new game or loads a previous one',
    'menu.nextgame': 'Notes that you want to play the next game and pings you when it is created',
    'menu.join': 'Joins you to an existing game (in reply, joins that player)',
    'menu.startgame': 'Starts a game once everybody has joined',
    'menu.board': 'Prints the current board',
    'menu.history': 'Prints the game history (compact or extended, remembered)',
    'menu.votes': 'Prints who has voted',
    'menu.calltovote': 'Tells the players it is time to vote (or the MVP if it already ended)',
    'menu.retirar': 'Withdraws your Ja or Nein vote so you can vote again',
    'menu.roles': 'How many roles and policies there are per player count',
    'menu.startautoja': 'Turns on your automatic Ja vote and lets you choose when it stops',
    'menu.stopautoja': 'Turns off your automatic Ja vote',
    'menu.conflicto': 'Turns off the automatic Ja vote for every player',
    'menu.info': 'Shows your private game information',
    'menu.jugadores': 'Shows the players in the game',
    'menu.leave': 'Removes you from an existing game',
    'menu.stats': 'Shows the stats',
    'menu.stats2': 'Shows your new stats linked to your ID',
    'menu.logros': 'Shows your unlocked achievements',
    'menu.guess': 'Privately guess who the fascists and Hitler are',
    'menu.mvp': 'Privately vote for the best player of the game',
    'menu.end': 'Closes the MVP vote without waiting for everybody',
    'menu.prueba': 'Marks the game as a test (no stats, achievements or MVP) or makes it count',
    'menu.guessresults': 'Reprints the guess results',
    'menu.miguess': 'Privately shows your own /guess result',
    'menu.version': 'Shows the current bot version',
    'menu.all': 'Mentions every known member of the group',
})
