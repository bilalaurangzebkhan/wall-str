import { useEffect, useState } from "react";

type TQuote = {
  text: string;
  author: string;
};

export function Quote() {
  const [currentQuote, setCurrentQuote] = useState<TQuote | null>(null);

  useEffect(() => {
    const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
    setCurrentQuote(randomQuote);
  }, []);

  return (
    <>
      {currentQuote && (
        <div className="flex flex-col items-center justify-center p-8 text-center max-w-2xl mx-auto -mt-10">
          <blockquote className="text-2xl font-serif italic text-base-content/70 mb-4">
            &quot;{currentQuote.text}&quot;
          </blockquote>
          <cite className="text-base-content/50 font-medium not-italic">{currentQuote.author}</cite>
        </div>
      )}
    </>
  );
}

const quotes: TQuote[] = [
  {
    text: "The four most dangerous words in investing are: 'this time it's different.'",
    author: "Sir John Templeton",
  },
  {
    text: "The stock market is a device for transferring money from the impatient to the patient.",
    author: "Warren Buffett",
  },
  {
    text: "Risk comes from not knowing what you're doing.",
    author: "Warren Buffett",
  },
  {
    text: "The intelligent investor is a realist who sells to optimists and buys from pessimists.",
    author: "Benjamin Graham",
  },
  {
    text: "Know what you own, and know why you own it.",
    author: "Peter Lynch",
  },
  {
    text: "The goal of a successful investor is to make the most money with the least risk and the greatest enjoyment.",
    author: "Philip Fisher",
  },
  {
    text: "Wide diversification is only required when investors do not understand what they are doing.",
    author: "Warren Buffett",
  },
  {
    text: "Investing should be more like watching paint dry or watching grass grow. If you want excitement, take $800 and go to Las Vegas.",
    author: "Paul Samuelson",
  },
  {
    text: "Opportunities come infrequently. When it rains gold, put out the bucket, not the thimble.",
    author: "Warren Buffett",
  },
  {
    text: "An investment in knowledge pays the best interest.",
    author: "Benjamin Franklin",
  },
  {
    text: "The stock market is filled with individuals who know the price of everything, but the value of nothing.",
    author: "Philip Fisher",
  },
  {
    text: "Investing isn’t about beating others at their game. It’s about controlling yourself at your own game.",
    author: "Benjamin Graham",
  },
  {
    text: "The investor’s chief problem—and even his worst enemy—is likely to be himself.",
    author: "Benjamin Graham",
  },
  {
    text: "Price is what you pay. Value is what you get.",
    author: "Warren Buffett",
  },
  {
    text: "It’s not whether you’re right or wrong that’s important, but how much money you make when you’re right and how much you lose when you’re wrong.",
    author: "George Soros",
  },
  {
    text: "Successful investing is about managing risk, not avoiding it.",
    author: "Benjamin Graham",
  },
  {
    text: "The stock market is never obvious. It is designed to fool most of the people, most of the time.",
    author: "Jesse Livermore",
  },
  {
    text: "The key to making money in stocks is not to get scared out of them.",
    author: "Peter Lynch",
  },
  {
    text: "Someone's sitting in the shade today because someone planted a tree a long time ago.",
    author: "Warren Buffett",
  },
  {
    text: "The individual investor should act consistently as an investor and not as a speculator.",
    author: "Benjamin Graham",
  },
  {
    text: "Wall Street makes its money on activity. You make your money on inactivity.",
    author: "Warren Buffett",
  },
  {
    text: "The function of economic forecasting is to make astrology look respectable.",
    author: "John Kenneth Galbraith",
  },
  {
    text: "Do not be embarrassed by your failures, learn from them and start again.",
    author: "Richard Branson",
  },
  {
    text: "Bull markets are born on pessimism, grow on skepticism, mature on optimism, and die on euphoria.",
    author: "Sir John Templeton",
  },
  {
    text: "It is not the strongest of the species that survive, nor the most intelligent, but the one most responsive to change.",
    author: "Charles Darwin",
  },
  {
    text: "Every once in a while, the market does something so stupid it takes your breath away.",
    author: "Jim Cramer",
  },
  {
    text: "Time in the market beats timing the market.",
    author: "Ken Fisher",
  },
  {
    text: "Earnings don’t move the overall market; it’s the Federal Reserve Board… focus on the central banks, and focus on the movement of liquidity.",
    author: "Stanley Druckenmiller",
  },
  {
    text: "The market can stay irrational longer than you can stay solvent.",
    author: "John Maynard Keynes",
  },
  {
    text: "If you have trouble imagining a 20% loss in the stock market, you shouldn't be in stocks.",
    author: "John Bogle",
  },
  {
    text: "Invest for the long haul. Don’t get too greedy and don’t get too scared.",
    author: "Shelby M.C. Davis",
  },
  {
    text: "We don’t have to be smarter than the rest. We have to be more disciplined than the rest.",
    author: "Warren Buffett",
  },
  {
    text: "Do not save what is left after spending, but spend what is left after saving.",
    author: "Warren Buffett",
  },
  {
    text: "In the short run, the market is a voting machine but in the long run, it is a weighing machine.",
    author: "Benjamin Graham",
  },
  {
    text: "Cash combined with courage in a time of crisis is priceless.",
    author: "Warren Buffett",
  },
  {
    text: "Compound interest is the eighth wonder of the world. He who understands it, earns it... he who doesn’t, pays it.",
    author: "Albert Einstein",
  },
  {
    text: "To achieve satisfactory investment results is easier than most people realize; to achieve superior results is harder than it looks.",
    author: "Benjamin Graham",
  },
  {
    text: "As long as you enjoy investing, you’ll be willing to do the homework and stay in the game.",
    author: "Jim Cramer",
  },
  {
    text: "Fear and greed are stronger than long-term resolve.",
    author: "Peter Bernstein",
  },
];
