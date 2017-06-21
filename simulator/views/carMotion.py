import matplotlib

def motion(self, env, s_max, initial_car_distance, run_direction):

    '''all is based on actualization of below statements 
    in next steps with 'step_size' incrementation:
    s = s0 + v0*(t) + (1/2)*a0*(t**2) + (1/6)*j*(t**3)
    v = v0 + a0*(t) + (1/2)*j*(t**2)
    a = a0 + j*(t)
    j = j0
    '''

    start_time = env.now
    
    step_size = 0.01        # movement incrementation
    t = 0                   # base time
    t2 = 0                  # additional time start when deceleration start

    s0 = 0
    v0 = 0
    a0 = 0
    j0 = self.jerk          # jerk [m/s3]
    
    s = 0
    v = 0
    a = 0
    j = j0
    
    vmax = self.speed
    amax = self.acceleration
    amin = -self.acceleration

    dActS = 0               # deceleration activation distance (s) before planned stop
    sTillEnd = s_max        # distance to end of planned way
    

    while s < s_max:        # run till reached demanded distance 's_max'
        t += step_size      # update base time in each step
        
        if s < 0.5*s_max:           # first half of demanded distance
            #history.append('przysp')
            if a < amax and v < vmax:
                #history.append('speed, accele, jerk', v, a, j, '  ', s)
                s = s0 + v0*(t) + (1/2)*a0*(t**2) + (1/6)*j*(t**3)
                s1 = s                                  # remember actual value to use it in next step if next "if" will be used
                v = v0 + a0*(t) + (1/2)*j*(t**2)        
                v1 = v                                  
                a = a0 + j*(t)
                s1t = s0 + v0*(t) + (1/2)*a*((t)**2)    # forecasted to be in next "if" 
                v1t = v0 + a*((t))                      # forecasted to be in next "if"
                dActS = s
                sTillEnd = s_max - s
            else:
                if a >= amax and v < vmax:
                    #history.append('speed, accele', v, a, '  ', s)
                    j = 0
                    s = -s1t + s1 + s0 + v0*(t) + (1/2)*a*(t**2)   #     subtract forecasted value in previous step
                                                                   # and subtract value form previous step
                                                                   # and add actual value
                                                                   # it is for leveling new function run with previous                                                                  
                    s2 = s
                    v = -v1t + v1 + v0 + a*(t)
                    s2t = s0 + v*(t)
                    dActS = s
                    sTillEnd = s_max - s
                else:
                    if (a >= amax or a == 0) and v >= vmax:
                        #history.append('speed', v, '  ', s)
                        j = 0
                        a = 0
                        s = -s2t + s2 + s0 + v*(t)
                        sTillEnd = s_max - s
            sk = s                  # it is for leveling new function run with previous     
            vk = v
            ak = a
 
        else:                       # second half of demanded distance
            if sTillEnd >= dActS:
                s = -s2t + s2 + s0 + v*(t)
                sTillEnd = s_max - s

                sk = s              # it is for leveling new function run with previous     
                vk = v
                ak = a
            else:
                if t2 == 0:
                    a = 0
                else:
                    pass
                
                t2 += step_size
                j = -j0             # start to decelerate
                v0 = vk             # state initial speed
                
                if v <= 0:
                    s = s_max
                    continue
                                   
                if 0 >= a and a > amin:
                    s =  sk + s0 + v0*(t2) + (1/2)*a0*(t2**2) + (1/6)*j*(t2**3)
                    s1 = s
                    v = v0 + a0*(t2) + (1/2)*j*(t2**2)
                    v1 = v
                    a = a0 + j*(t2)
                    at = a
                    s1t = s0 + v0*(t2) + (1/2)*a*(t2**2)
                    v1t = v0 + a*(t2)
                    sTillEnd = s_max - s

                else:
                    if a <= amin and v > 0:
                        j = 0
                        a = at
                        s = -s1t + s1 + s0 + v0*(t2) + (1/2)*a*(t2**2)
                        v = -v1t + v1 + v0 + a*(t2)
                        sTillEnd = s_max - s

        yield env.timeout(step_size)

        self.carMovement[0].append(start_time + t)
        self.carMovement[1].append(initial_car_distance + (run_direction * s))
        self.carMovement[2].append(v)
        self.carMovement[3].append(a)
