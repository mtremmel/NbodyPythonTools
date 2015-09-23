import nbdpt.rockstar.rockstarscript as rs
import os 

rockstardir   = '/u/sciteam/tremmel/Scripts/Rockstar-Galaxies/'
nnodes        = 1
ncorespernode = 32 
queue         = 'high'                 #largemem, normal on stampede
email         = 'm.tremmel6@gmail.com'  #please change so I don't get all your emails :P
machine       = 'bluewaters'                 #stampede, pleiades, bluewaters or interactive
walltimemain  = '24:00:00'                 #need to use this notation 
walltimepost  = '3:00:00'
massdef       = '200c'                     #mass options, 'vir', '###b', '###c'
massdef2      = None
ServerInterface = 'ipogif0'                    #'ipogif0' on bluewaters
fileformat = 'TIPSY'
snapsPerRun = 3   #number of snapshots per run of rockstar... for large simulations, keep relatively low. 2-3 probably for cosmo25
cleanup = True    #True = delete the raw rockstar output, which is no longer needed after post processing.
nmin = 128
nread = 256

if not os.path.exists('rockstarfiles'): os.system('mkdir rockstarfiles')

def make():
    rs.snaps(snapsPerRun)
    rs.cfg(ncorespernode=ncorespernode, nnodes=nnodes, 
           ServerInterface=ServerInterface, massdef=massdef, 
           massdef2=massdef2, fileformat=fileformat,nmin=nmin,nread=nread) 
    rs.mainsubmissionscript(nnodes=nnodes, ncorespernode=ncorespernode, 
                            machine=machine, email=email, 
                            rockstardir=rockstardir, queue=queue, walltime=walltimemain)
    rs.postsubmissionscript(nnodes=nnodes, ncorespernode=ncorespernode,
                            machine=machine, email=email, 
                            rockstardir=rockstardir, queue=queue, walltime=walltimepost, fileformat=fileformat,cleanup=cleanup,nmin=nmin)
    
#then submit rockstar.sbatch to the queue, and rockstar.post.sbatch to the queue 
#    depending on the prior finishing ok

#sbatch rockstar.sbatch
#sbatch --dependency=afterok:<jobid> rockstar.post.sbatch

if __name__=='__main__': make()
