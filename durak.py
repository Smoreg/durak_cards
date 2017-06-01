import random
from abc import ABCMeta, abstractmethod
from itertools import chain


class Card:
    not_nums = dict(zip(range(11, 17), 'JQKA00'))

    # trump = None

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __gt__(self, other):
        if self.suit == other.suit:
            return self.rank > other.rank
            # elif self.suit == self.trump:
            #    return True

    def __repr__(self):
        if int(self.rank) > 10:
            rank = self.not_nums[self.rank]
        else:
            rank = self.rank
        return str(rank) + self.suit


class Deck:
    not_nums = dict(zip(range(11, 15), 'JQKA'))

    def __init__(self, local_card, french=False, jokers=False, empty=False):
        self.Card = local_card
        min_rank = 2 if french else 6
        ranks = [n for n in range(min_rank, 15)]
        suits = list('♠♥♣♦')
        self.cards = [self.Card(rank, suit) for rank in ranks for suit in suits]
        if empty:
            self.cards = []

    def __len__(self):
        return len(self.cards)

    def __getitem__(self, position):
        return self.cards[position]

    def __repr__(self):
        return str(self.cards)

    def __bool__(self):
        return bool(self.cards)

    def get_upper_cards(self, num=None):
        if num == None:
            return self.cards.pop()
        else:
            hand = []
            for i in range(num):
                if self:
                    hand.append(self.cards.pop())
            return hand

    def shuffle(self):
        random.shuffle(self.cards)

    def draw_cards(self, num_players, num_cards):
        result = [[] for _ in range(num_players)]
        for card in range(num_cards):
            for player in range(num_players):
                result[player].append(self.get_upper_cards())
        return result

    def put_in_end(self, card):
        self.cards.insert(0, card)

    def current_size(self):
        return len(self.cards)

    def extend(self, *args, **kwargs):
        return self.cards.extend(*args, **kwargs)

    def append(self, *args, **kwargs):
        return self.cards.append(*args, **kwargs)


class Hand(Deck):
    def __init__(self, local_card, cards=None):
        super().__init__(local_card=local_card, empty=True)
        if cards:
            self.cards = cards

    def filter(self, **filters):
        """

        :param filters: suit , rank_gt, rank_lt, rank_gte, rank_lte, rank_min, rank_max
        :return:
        """

        cards = self.cards
        for card_filter in filters:
            if cards:
                if 'suit' == card_filter:
                    cards = filter(lambda card: card.suit == filters[card_filter], cards)
                elif card_filter == 'rank_gt':
                    cards = filter(lambda card: card.rank > filters[card_filter], cards)
                elif card_filter == 'rank_gte':
                    cards = filter(lambda card: card.rank >= filters[card_filter], cards)
                elif card_filter == 'rank_lt':
                    cards = filter(lambda card: card.rank < filters[card_filter], cards)
                elif card_filter == 'rank_lte':
                    cards = filter(lambda card: card.rank <= filters[card_filter], cards)
                # elif card_filter == 'rank_min':
                #     cards = [min(cards), ]
                # elif card_filter == 'rank_max':
                #     cards = [max(cards), ]
                else:
                    raise Exception('Bad filter')
        return Hand(local_card=self.Card, cards=list(cards))

    def get_card(self, index):
        return self.cards.pop(index)


class IPlayer(metaclass=ABCMeta):
    def __init__(self, name='No_name', human=False, game=None):
        self.game = game
        self.name = name
        self.human = human
        self.hand = Hand(local_card=game.LocalCard)
        self.attack_flag = False

    def __repr__(self):
        return self.name + str(self.hand) + "\n"

    @abstractmethod
    def attack(self):
        pass

    @abstractmethod
    def defend(self):
        pass

    @abstractmethod
    def shortage(self):
        pass

    def hand_size(self):
        return len(self.hand)


class HumanPlayer(IPlayer):
    @classmethod
    def user_link(*args, **kwargs):
        print(chr(27) + "[2J")
        print(*args, **kwargs)
        card_num = 0
        while True:
            try:
                card_num = int(input())
                break
            except ValueError:
                "Print number"
        return card_num

    def __init__(self, *args, **kwargs):
        super().__init__(*args, human=True, **kwargs)
        # self.user_link('Hello {}! Lets kick some card ass! Press Enter to continue'.format(str(id(self))))

    def get_field_view(self):
        game = self.game
        field_view = list()
        field_view.append('Durak GAME'.center(100, "#"))
        field_view.append('Enemy'.center(100, "-"))
        for player in game.players:
            if player.name != self.name:
                field_view.append('{}: {}'.format(player.name, '# ' * player.hand_size()))
        field_view.append('Deck'.center(100, "-"))
        field_view.append('{} more cards. Trump is {}'.format(game.deck.current_size(), game.trump).center(100, " "))
        field_view.append('Field'.center(100, "-"))

        field = game.field
        beaten_cards = ''
        for card in field.beaten_cards:
            beaten_cards += " {} ".format(repr(card))
        field_view.append(beaten_cards)
        field_view.append('')
        field_view.append((repr(field.attack_card) if field.attack_card else '').center(100, ' '))

        field_view.append(''.center(100, "-"))
        field_view.append('My cards'.center(100, "-"))
        my_cards = ''

        for num, card in enumerate(self.hand):
            info = ''
            if self.attack_flag:
                if self.game.field.ranks and card.rank in self.game.field.ranks:
                    info = 'THROW:'
            else:
                attacker = self.game.field.attack_card
                if attacker.suit == self.game.trump:
                    if card.suit == self.game.trump and card.rank > attacker.rank:
                        info = 'DEFEND:'
                else:
                    if card.suit == self.game.trump:
                        info = 'DEFEND:'
                    elif card.suit == attacker.suit and card.rank > attacker.rank:
                        info = 'DEFEND:'

            my_cards += "{}{}:{}       ".format(info, num, card)

        field_view.append(my_cards.center(100, " "))
        field_view.append(''.center(100, "-"))
        field_view.append('Choose card'.center(100, " "))
        field_view.append('')

        result = '\n'
        for line in field_view:
            result += str(line) + '\n'
        return result

    def attack(self):
        num = self.user_link(self.get_field_view())
        try:
            return self.hand.get_card(num)
        except IndexError:
            return None

    def defend(self):
        num = self.user_link(self.get_field_view())
        try:
            return self.hand.get_card(num)
        except IndexError:
            return None

    def shortage(self):
        need = self.game.cards_num - self.hand_size()
        if need >= 0:
            for card in self.game.deck.get_upper_cards(need):
                self.hand.put_in_end(card)


class AIDuel(IPlayer):
    def __init__(self, name='', human=False):
        super().__init__(name, human)

    def __repr__(self):
        return self.name + str(self.hand) + "\n"


class Field:
    def __init__(self, game):
        self.attack_card = None
        self.beaten_cards = list()
        self.ranks = set()
        self.capacity = 6
        self.game = game

    def attack(self, player):
        card = None

        if not player.hand_size() or not self.capacity:
            return 'defend win'

        while True:
            card = player.attack()

            if not card:
                self.attack_card = None
                return 'defend win'

            if self.ranks and card.rank not in self.ranks:
                player.hand.append(card)
                print('BAd attack')
            else:
                self.capacity -= 1
                self.attack_card = card
                self.ranks.add(card.rank)
                return ''

    def defend(self, player):
        if not player.hand_size() or not self.attack_card:
            return 'defend win'
        while True:
            card = player.defend()
            if not card:
                self.result = False  # attacker win
                return 'attack win'

            if card > self.attack_card:
                self.beaten_cards.extend([self.attack_card, card])
                self.ranks.add(card.rank)
                self.attack_card = None
                return ''
            else:
                player.hand.append(card)
                print('BAd defend')


class Game:
    trump = None
    turn = None
    run = True
    field = None

    class LocalCard(Card):
        trump = None

        def __gt__(self, other):
            if self.suit == other.suit:
                return self.rank > other.rank
            elif self.suit == self.trump:
                return True

    def __init__(self, players_classes):
        self.deck = Deck(local_card=self.LocalCard)
        self.deck.shuffle()
        self.players = [player(name="{}-{}".format(player.__name__, num + 1), game=self) for num, player in
                        enumerate(players_classes)]
        self.players_num = len(players_classes)
        self.cards_num = 6
        self.winner = None

    def draw_cards(self):
        [setattr(player.hand, 'cards', cards) for player, cards in
         zip(self.players, self.deck.draw_cards(self.players_num, self.cards_num))]

    def choice_first(self):
        min([]) if [] else 123
        start_hands = [player.hand.filter(suit=self.trump) for player in self.players]
        start_hands = [min(hand.cards) if hand.cards else self.LocalCard(15, self.trump) for hand in start_hands]
        return start_hands.index(min(start_hands))

    def restore_cards(self):
        queue = chain(range(self.turn, self.players_num), range(0, self.turn))
        for player in [self.players[num] for num in queue]:
            player.shortage()

    def preparations(self):
        # start
        self.draw_cards()
        trump_card = self.deck.get_upper_cards()
        self.deck.put_in_end(trump_card)
        self.trump = trump_card.suit
        self.LocalCard.trump = trump_card.suit
        self.turn = self.choice_first()

    def get_attacker_player(self):
        return self.players[self.turn]

    def get_defender_player(self):
        return self.players[(self.turn + 1) % self.players_num]

    def next_turn(self):
        self.get_attacker_player().attack_flag = False
        self.get_defender_player().attack_flag = True
        self.turn = (self.turn + 1) % self.players_num

    def finish_check(self):
        hands_size = [player.hand_size() for player in self.players]
        if not all(hands_size):
            if hands_size.count(0) > 1:
                self.winner = 'draw'
                return True
            else:
                self.winner = str(hands_size.index(0))
                return True
        else:
            return False


class GameDuel(Game):
    current_turn = None

    def __init__(self, player1, player2):
        super().__init__([player1, player2])

    def play_loop(self):
        self.get_attacker_player().attack_flag = True

        while self.run:
            # start turn.
            attacker_player = self.get_attacker_player()
            defender_player = self.get_defender_player()
            self.current_turn = True
            self.field = Field(Game)
            while self.current_turn:
                result_attack = self.field.attack(attacker_player)
                result_defend = self.field.defend(defender_player)
                result = result_attack or result_defend
                if result:
                    self.current_turn = False
                    if result == 'attack win':
                        defender_player.hand.extend(self.field.beaten_cards)
                        defender_player.hand.append(self.field.attack_card)
                    elif result == 'defend win':
                        self.next_turn()

            self.restore_cards()

            if self.finish_check():
                self.run = False
                break

        return self.winner


for i in range(100):
    game = GameDuel(*[HumanPlayer] * 2)
    game.preparations()
    print('---------------' + game.play_loop() + '----------------')
