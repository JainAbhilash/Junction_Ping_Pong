import time
from collections import deque

import torch
import torch.nn.functional as F

from envs import ObsNorm
from model import ActorCritic
from pong import Pong
from simple_ai import PongAi

import numpy as np
import matplotlib.pyplot as plt

from scipy.interpolate import make_interp_spline, BSpline
from scipy.ndimage.filters import gaussian_filter1d as gf


def test(rank, args, shared_model, counter, optimizer, testValue):
    torch.manual_seed(args.seed + rank)

    env = Pong(headless= args.headless)
    # env.seed(args.seed + rank)

    model = ActorCritic(1, 3)
    
    opponent = PongAi(env, 2)
    obsNorm = ObsNorm()
    model.eval()

    env.set_names('RL Agent', opponent.get_name())
    state = obsNorm.prepro(env.reset()[0])
    
    state = torch.from_numpy(state)
    reward_sum = 0
    done = True

    start_time = time.time()
    
    # a quick hack to prevent the agent from stucking
    actions = deque(maxlen=100)
    episode_length = 0
    save_count = 0
    test_count = 0
    distr = np.zeros((235,3))
    while True:
        testValue.put(['test']) 
        env.render()
        episode_length += 1
        # Sync with the shared model
        if done:
            model.load_state_dict(shared_model.state_dict())
            cx = torch.zeros(1, 256)
            hx = torch.zeros(1, 256)
        else:
            cx = cx.detach()
            hx = hx.detach()

        with torch.no_grad():
            inputTensor = state.unsqueeze(0);
            value, logit, (hx, cx) = model((inputTensor, (hx, cx)))
        prob = F.softmax(logit, dim=-1)
        action = prob.max(1, keepdim=True)[1].numpy()
        
        ###
        pos = int(env.player1.y - env.player1.h/2)
        probz = prob.squeeze(0)
        distr[pos, 0] += probz[0]
        distr[pos, 1] += probz[1]
        distr[pos, 2] += probz[2]
        ###

        action2 = opponent.get_action()
        
        (state, obs2), (reward, reward2), done, info = env.step((action[0,0], action2))
        done = done or episode_length >= args.max_episode_length
        reward_sum += reward
        state = obsNorm.prepro(state)
        # a quick hack to prevent the agent from stucking
        actions.append(action[0, 0])
        if actions.count(actions[0]) == 5000:
            done = True
            test_count += 1
            
        if done:
            test_count += 1
            print("Time {}, num steps {}, FPS {:.0f}, episode reward {}, episode length {}".format(
                time.strftime("%Hh %Mm %Ss",
                              time.gmtime(time.time() - start_time)),
                counter.value, counter.value / (time.time() - start_time),
                reward_sum, episode_length))
            reward_sum = 0
            episode_length = 0
            actions.clear()
            obsNorm.reset()
            state = obsNorm.prepro(env.reset()[0])
            ####
            summ = distr.sum()
            distrs = []
            dsums = []
            xnew = np.arange(0, 235)
            for i in range(3):
                int_distr = gf(distr[:,i], sigma=2)
                distrs.append(int_distr)
                dsums.append(int_distr.sum())
            plt.clf()
            plt.grid(True)
            plt.plot(xnew, distrs[0]/dsums[0], alpha=0.4, lw=2, label='STAY')
            plt.plot(xnew, distrs[1]/dsums[1], alpha=0.4, lw=2, label='MOVE UP')
            plt.plot(xnew, distrs[2]/dsums[2], alpha=0.4, lw=2, label='MOVE DOWN')
            plt.xlabel("Paddle y-position")
            plt.ylabel("Mean density of actions (gaussian filtered)")
            plt.legend()
            plt.title('Action space distribution vs paddle positions')
            plt.draw()
            plt.pause(0.0001)
            ####
        if save_count == 10:
            if args.save_progress:
                save_checkpoint(shared_model, optimizer, 'checkpoint-ob')
            save_count = 0
        if test_count == 10:
            save_count += 1
            test_count = 0
            #time.sleep()
            
        state = torch.from_numpy(state)

def save_checkpoint(model, optimizer, filename='/output/checkpoint.pth.tar'):
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
        }, filename)
