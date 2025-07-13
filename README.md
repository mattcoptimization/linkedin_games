# LinkedIn Queens Solver

Over the last few weeks, I have found myself wasting a whole 2-3 minutes a day solving the LinkedIn Queens daily game. 
Following in the footsteps of the New York Times, LinkedIn has attempted to boost daily engagement by providing daily "challenges".
Somewhere along the way, I became curious. 
Could I solve this using mathematical optimization? What about using constraint programming?
I had also recently learned how to use the library `playwright`. 
Traditionally used for testing web interfaces, it can also be used to script web interactions in real world websites.
Famously, the Rabbit R1 "Large Action Model" (their words, not mine) [used an LLM to invoke pre-written scripts](https://ainiro.io/blog/rabbit-r1-textbook-ai-based-pump-and-dump).

## The Game

![Solved Puzzle](image.png)

The [Queens Game](https://www.linkedin.com/games/queens/) has 3 main rules:

1. Each unique color region must have exactly one queen.
2. Each row and column must have exactly one queen.
3. Queens cannot directly border one another (think a king in a game of Chess)

Simple, right?

Let's solve this "the normal way".

On the left hand side, two columns share two colors. This means that the other colors cannot have a queen. We combine rules 1 and 2 above to say that no queens can be in the first or second column for light blue and red. 

![Puzzle Step 1](image_copy.png)

On the right hand side, red is the only available color. This means the rest of the red should be blocked out.
![Puzzle Step 2](image_copy_2.png)

In the middle, the yellow row means that no other color can have a queen in that row. This is the only option for the yellow color.
![Puzzle Step 3](image_copy_3.png)

We keep going, combining constraints until only one solution is possible.
If we solve fast enough, we get a flashy solution screen! 
We get to compare ourselves to our peers. 
How many CEOs am I "smarter" than? Where do I fall in the LinkedIn hierarchy?

After two weeks of solving these puzzles, I decided I was tired of being in the middle 50% of solve times.
As Ash Ketchum would say, I want to be the very best.
And I'm going to use programming and optimization to cheat.

## The Model

For this problem, I decided to use Google's CP-SAT solver in ORTools? 
Could I have used a traditional IP solver?
Yes.
Why did I use this one?
Honestly, just because I don't have a ton of experience with SAT solvers.
I wanted to try out the solver interface.

For those unfamiliar, constraint programming focuses on problems where all variables are integers.
In mathematical optimization, variables are decisions to be made by the model, constraints are restrictions
placed on the variables in these problems, and parameters are fixed values given in the problem statement.

Lets define each of these for our problem:
1. Variables: Whether or not a specific cell has a queen. This means we have NxN number of variables. If 0, the cell does not have a queen. If 1, the cell does have a queen.
```python
{(i,j): model.NewBoolVar(f"queen_{i}_{j}") for i in range(n_size) for j in range(n_size)}
```
2. Parameters: The color of each cell. For efficiency reasons later, it is best to store this in a dictionary of `{color: [list_of_cells_of_that_color]}`
3. Constraints. Here is where things get a little more complicated:
    * One queen per row
    * One queen per column
    * No adjacent queens
    * One queen per color

We can represent these in LaTeX below:

Now that we have our problem, we can write it out fully in code like the following: 


## The Script

To solve the puzzle as fast as possible