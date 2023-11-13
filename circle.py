def WritePixel(x, y, r):
    print("(%d, %d)" % (x, y))
    plot([x], [y], '.')

def CirclePoints(x, y, i, j, r, writepix):
    writepix(i+x, j+y, r)
    writepix(i+y, j+x, r)
    writepix(i+y, j-x, r)
    writepix(i+x, j-y, r)
    writepix(i-x, j-y, r)
    writepix(i-y, j-x, r)
    writepix(i-y, j+x, r)
    writepix(i-x, j+y, r)

def MidpointCircle(i, j, radius, writepix=WritePixel):
    # Uses second-order partial derivatives to compute
    # increments in the decision variable.
    # Assumes circle center at i, j.
    # Algorithm by Bresenham 1977
    x = 0
    y = radius
    d = 1 - radius
    deltaE = 3
    deltaSE = -2 * radius + 5
    CirclePoints(x, y, i, j, radius, writepix)

    while y > x:
        if d < 0:
            d = d + deltaE
            deltaE += 2
            deltaSE += 2
            x = x + 1
        else:
            d = d + deltaSE
            deltaE += 2
            deltaSE += 4
            x = x + 1
            y = y - 1
        CirclePoints(x, y, i, j, radius, writepix)
        
