#-------------------------------------------------------------------------------
# Iteratively estimates a trajectory by using gradient descent to try and
# minimise the error between predicted and observed landmark bearings
#-------------------------------------------------------------------------------

import random
import math

class TrajectoryEstimator:

    USE_VISIBILTY = True

    #---------------------------------------------------------------------------
    def __init__( self ):
        pass

    #---------------------------------------------------------------------------
    def landmarkError( self, rX, rY, rTheta, lX, lY, b ):
        xDiff = (rX - lX)
        yDiff = (rY - lY)
        distToLandmark = math.sqrt( xDiff**2 + yDiff**2 )
        if distToLandmark == 0.0:
            return 2.0
        else:
            return ( yDiff*math.sin( rTheta + b ) + xDiff*math.cos( rTheta + b ) ) / distToLandmark

    #---------------------------------------------------------------------------
    def landmarkError_dx( self, rX, rY, rTheta, lX, lY, b ):
        
        sinAngle = math.sin( rTheta + b )
        cosAngle = math.cos( rTheta + b )
        xDiff = (rX - lX)
        yDiff = (rY - lY)
        distToLandmark = math.sqrt( xDiff**2 + yDiff**2 )
    
        return -(xDiff*( yDiff*sinAngle + xDiff*cosAngle )) / (distToLandmark**3) \
            + cosAngle/distToLandmark

    #---------------------------------------------------------------------------
    def landmarkError_dy( self, rX, rY, rTheta, lX, lY, b ):
        
        sinAngle = math.sin( rTheta + b )
        cosAngle = math.cos( rTheta + b )
        xDiff = (rX - lX)
        yDiff = (rY - lY)
        distToLandmark = math.sqrt( xDiff**2 + yDiff**2 )
        
        return -(yDiff*( yDiff*sinAngle + xDiff*cosAngle )) / (distToLandmark**3) \
            + sinAngle/distToLandmark

    #---------------------------------------------------------------------------
    def landmarkError_dTheta( self, rX, rY, rTheta, lX, lY, b ):
                    
        sinAngle = math.sin( rTheta + b )
        cosAngle = math.cos( rTheta + b )
        xDiff = (rX - lX)
        yDiff = (rY - lY)
        distToLandmark = math.sqrt( xDiff**2 + yDiff**2 )
        
        return ( yDiff*cosAngle - xDiff*sinAngle ) / distToLandmark

    #---------------------------------------------------------------------------
    def frameError( self, frameIdx ):
        
        poseGuess = self.poseGuesses[ frameIdx ]
        bearings = self.observedBearings[ frameIdx ]
        visibilty = self.landmarkVisibility[ frameIdx ]

        error = 0.0
        for landmarkIdx, landmarkPos in enumerate( self.landmarkPositions ):

            if not self.USE_VISIBILTY \
                or visibilty[ landmarkIdx ]:

                error += self.landmarkError( poseGuess[ 0 ], poseGuess[ 1 ], 
                    poseGuess[ 2 ], landmarkPos[ 0 ], landmarkPos[ 1 ],
                    bearings[ landmarkIdx ] )

        return error

    #---------------------------------------------------------------------------
    def frameError_dx( self, frameIdx ):
        
        poseGuess = self.poseGuesses[ frameIdx ]
        bearings = self.observedBearings[ frameIdx ]
        visibilty = self.landmarkVisibility[ frameIdx ]

        error = 0.0
        for landmarkIdx, landmarkPos in enumerate( self.landmarkPositions ):

            if not self.USE_VISIBILTY \
                or visibilty[ landmarkIdx ]:

                error += self.landmarkError_dx( poseGuess[ 0 ], poseGuess[ 1 ], 
                    poseGuess[ 2 ], landmarkPos[ 0 ], landmarkPos[ 1 ],
                    bearings[ landmarkIdx ] )

        return error

    #---------------------------------------------------------------------------
    def frameError_dy( self, frameIdx ):
        
        poseGuess = self.poseGuesses[ frameIdx ]
        bearings = self.observedBearings[ frameIdx ]
        visibilty = self.landmarkVisibility[ frameIdx ]

        error = 0.0
        for landmarkIdx, landmarkPos in enumerate( self.landmarkPositions ):

            if not self.USE_VISIBILTY \
                or visibilty[ landmarkIdx ]:

                error += self.landmarkError_dy( poseGuess[ 0 ], poseGuess[ 1 ], 
                    poseGuess[ 2 ], landmarkPos[ 0 ], landmarkPos[ 1 ],
                    bearings[ landmarkIdx ] )

        return error

    #---------------------------------------------------------------------------
    def frameError_dTheta( self, frameIdx ):
        
        poseGuess = self.poseGuesses[ frameIdx ]
        bearings = self.observedBearings[ frameIdx ]
        visibilty = self.landmarkVisibility[ frameIdx ]

        error = 0.0
        for landmarkIdx, landmarkPos in enumerate( self.landmarkPositions ):

            if not self.USE_VISIBILTY \
                or visibilty[ landmarkIdx ]:

                error += self.landmarkError_dTheta( poseGuess[ 0 ], poseGuess[ 1 ], 
                    poseGuess[ 2 ], landmarkPos[ 0 ], landmarkPos[ 1 ],
                    bearings[ landmarkIdx ] )

        return error

    #---------------------------------------------------------------------------
    def estimateTrajectory( self, poseGuesses, landmarkPositions, observedBearings,
                            landmarkVisibility ):

        self.poseGuesses = poseGuesses
        self.landmarkPositions = landmarkPositions
        self.observedBearings = observedBearings
        self.landmarkVisibility = landmarkVisibility

        self.numFrames = len( poseGuesses )
        self.numLandmarks = len( landmarkPositions )

        MAX_NUM_VISIBLE_LANDMARKS = 2

        if self.USE_VISIBILTY:
            OK_FRAME_ERROR = -1.0*MAX_NUM_VISIBLE_LANDMARKS + 0.5
        else:
            OK_FRAME_ERROR = -1.0*self.numLandmarks + 0.5
        
        # Estimate the pose for the first frame
        self.minimiseFrameError( 0 )
        totalError = prevFrameError = self.frameError( 0 )

        # For each remaining frame
        for frameIdx in range( 1, self.numFrames ):

            # Use the previous pose if the frame error wasn't too bad
            if prevFrameError < OK_FRAME_ERROR:
                pass
                #self.poseGuesses[ frameIdx ] = self.poseGuesses[ frameIdx - 1 ]
            else:
                # Otherwise pick a new heading at random
                self.poseGuesses[ frameIdx ][ 2 ] = random.uniform( -math.pi, math.pi )

            # Estimate the pose for this frame
            self.minimiseFrameError( frameIdx )
            prevFrameError = self.frameError( frameIdx )

            # Update total error
            totalError += prevFrameError

        return totalError

    #---------------------------------------------------------------------------
    def minimiseFrameError( self, frameIdx ):

        MAX_NUM_ITERATIONS = 100
        EPSILON = 0.002
        numIterations = 0
    
        while numIterations < MAX_NUM_ITERATIONS:

            x = self.poseGuesses[ frameIdx ][ 0 ]
            y = self.poseGuesses[ frameIdx ][ 1 ]
            theta = self.poseGuesses[ frameIdx ][ 2 ]

            deltaX = self.frameError_dx( frameIdx )
            deltaY = self.frameError_dy( frameIdx )
            deltaTheta = self.frameError_dTheta( frameIdx )
                        
            frameGradientLength = math.sqrt( 
                deltaX**2 + deltaY**2 + deltaTheta**2 )
            
            if frameGradientLength < EPSILON:
                break        
            
            # Steepest descent is -ve jacobian
            gradX = -deltaX
            gradY = -deltaY
            gradTheta = -deltaTheta
    
            curVal = self.frameError( frameIdx )
            
            # Use back tracking line search
            alpha = 0.3
            beta = 0.8
            t = 1
        
            while 1:
                self.poseGuesses[ frameIdx ][ 0 ] = x + t*gradX
                self.poseGuesses[ frameIdx ][ 1 ] = y + t*gradY
                self.poseGuesses[ frameIdx ][ 2 ] = theta + t*gradTheta
                
                newVal = self.frameError( frameIdx )
                comparisonVal = curVal + alpha*t*( 
                    deltaX*gradX + deltaY*gradY + deltaTheta*gradTheta )

                if newVal > comparisonVal:
                    t = beta*t
                else:
                    #print "t set to", t
                    break
            
            numIterations += 1
        
        #print "Took", numIterations, "iterations"
        #print curPoint
        #return curPoint, points 