"""
The basic functions to create usable rockstar scripts to run rockstar on all tipsy
outputs in a directory. 

snaps()
  create a snaps.txt file containing all the outputs in the directory
  one number per line

cfg(ncorespernode=32, nnodes=1, ServerInterface='ipogif0', massdef='200c', massdef2=None)
  create a rockstar.submit.cfg file to submit to the rockstar program
  nocorespernode: the number of cores on each node of the computer
  ServerInterface: 'ib0' for most computers except bluewaters which uses 'ipogif0'
  massdef: how to define the virial mass of a halo 
  massdef2: if you want another mass defined

mainsubmissionscript(walltime = '24:00:00', email = 'l.sonofanders@gmail.com', machine='stampede', nnodes=1, ncorespernode=32, queue='largemem', rockstardir='/home1/02575/lmanders/code/Rockstar-Galaxies/')
  create the submission script to run rockstar. 
  walltime: total amount of wallclock time alloted to the analysis
  email: the email you want messages from the queue sent to
  machine: the machine you will run the process on; 
           right now either 'stampede', 'pleiades' or 'bluewaters'
  nnodes: the number of nodes to run on
  ncorespernode: the number of cores per node on the machine
  queue: the queue to submit to
  rockstardir: the directory your rockstar copy lies in

postsubmissionscript(email = 'l.sonofanders@gmail.com', machine = 'stampede', queue = 'largemem'\
, rockstardir='/home1/02575/lmanders/code/Rockstar-Galaxies', ncorespernode=32, walltime='24:00:00')
  create the submission script to do post processing on rockstar and turn its natural outputs 
  into .grp and .stat files
  email: the email you want messages from the queue sent to
  machine: the machine you will run the process on; 
           right now either 'stampede', 'pleiades', or 'bluewaters' 
  queue: the queue to submit to 
  rockstardir: the directory your rockstar copy lies in 
  ncorespernode: the number of cores per node on the machine 
  walltime: total amount of wallclock time alloted to the analysis
"""


import glob
import numpy as np
import struct
from .. import nptipsyreader
import os
from .. import findtipsy

def snaps(snapsPerRun,basedir='.'):
    fcnt = 0
    cnt = 0
    files = findtipsy.find(basedir=basedir)
    files.sort()
#    snaps = []
#    f = open('snaps.txt', 'w')
    for i in files: 
	if cnt%snapsPerRun==0:
		if fcnt != 0: f.close()
		fcnt+=1
		f = open('snaps'+str(fcnt)+'.txt','w')
		f.write(i.split('.')[-1] + '\n')
	else:
		f.write(i.split('.')[-1] + '\n')
	cnt+=1
    f.close()
    return

def cfg(ncorespernode=32, nnodes=1, ServerInterface='ipogif0', massdef='200c', massdef2=None, fileformat='TIPSY', basedir='.',nmin=20,nread=1):
    snapfiles = glob.glob('snaps*.txt')
    nsnapfiles = len(snapfiles)
    tipsyfile = findtipsy.find(basedir=basedir) #('.').join(glob.glob('*.iord')[0].split('.')[:-1])
    tipsyfile.sort()
    tipsyfile = tipsyfile[0]
    f = open(snapfiles[0])
    snap = f.readline().strip('\n')
    filename = basedir + '/' +  '.'.join(tipsyfile.split('.')[:-1])
    tipsy = nptipsyreader.Tipsy(filename + '.' + snap)
    tipsy._read_param()
    print tipsy.filename
    dmsol = np.float(tipsy.paramfile['dMsolUnit'])
    dkpc = np.float(tipsy.paramfile['dKpcUnit'])
    if tipsyfile.split('/')[-1][0] == 'h':
        tipsy._read()
        darkmass = np.min(tipsy.dark['mass'])*dmsol*tipsy.h
        force = np.min(tipsy.dark['eps'])*dkpc*tipsy.h/1e3*4.
    if (tipsyfile.split('/')[-1][0:5] == 'cosmo')or (tipsyfile.split('/')[-1][0:7] == 'romulus'):
        if fileformat == 'NCHILADA':
            f = open(filename+'.'+snap+'/dark/mass')
            (magic, time, iHighWord, nbodies, ndim, code) = struct.unpack('>idiiii', f.read(28))
            mass = struct.unpack('>f4', f.read(4))[0]
            f.close()
            f = open(filename+'.'+snap+'/dark/soft')
            (magic, time, iHighWord, nbodies, ndim, code) = struct.unpack('>idiiii', f.read(28))
            eps = struct.unpack('>f4', f.read(4))[0]
        else:
            f = open(filename+'.'+snap)
            (t, nbodies, ndim, nsph, ndark, nstar) = struct.unpack('>diiiii', f.read(28))
            f.seek(struct.calcsize('>diiiiii')+struct.calcsize('12f4')*nsph)
            (mass, x, y, z, vx, vy, vz, eps, phi) = struct.unpack('>9f4', f.read(36))
        darkmass = mass*dmsol*tipsy.h
    #f.seek(struct.calcsize('>diiiiii')+struct.calcsize('12f4')*nsph+struct.calcsize('9f4')*ndark)
    #(mass,x,y,z,vx,vy,vz,metals,tform,eps,phi) = struct.unpack('>11f4', f.read(44))
        force = eps*dkpc*tipsy.h/1e3
        f.close()
    
    for ii in range(nsnapfiles): 
	    f = open('rockstar.submit.'+str(ii+1)+'.cfg', 'w')
	    if basedir: f.write('INBASE=' + basedir + '\n')
	    f.write('OVERLAP_LENGTH=0.5 \n')
	    f.write('PARALLEL_IO=1 \n')
	    f.write('NUM_WRITERS=' + str(ncorespernode*nnodes)+' \n')
	    f.write('NUM_BLOCKS='+str(nread)+' \n')
	    f.write('FILENAME=' + filename +'.<snap> \n')
	    f.write('#NUM_SNAPS=1 \n')
	    f.write('SNAPSHOT_NAMES=snaps'+str(ii+1)+'.txt  #One snapshot name per line \n')
	    f.write('FORK_READERS_FROM_WRITERS=1 \n')
	    f.write('FORK_PROCESSORS_PER_MACHINE=' + str(ncorespernode) + '\n')
	    f.write('FILE_FORMAT = "' + fileformat + '" # or "ART" or "ASCII" \n')
	    f.write('PARTICLE_MASS ='+ str(darkmass) +'  #Msol/h \n')
	    f.write('FORCE_RES = ' + str(force) + '  #Mpc/h \n')                                            
	    f.write('# You should specify cosmology parameters only for ASCII formats \n# For GADGET2 and ART, these parameters will be replaced with values from the \n# particle data file \n')
	    f.write('MIN_HALO_PARTICLES = ' + str(nmin) + '\n')
	    f.write('MIN_HALO_OUTPUT_SIZE = ' + str(nmin) + '\n')
	    f.write('h0 =' + str(tipsy.h) + '\n')
	    f.write('Ol =' + tipsy.paramfile['dLambda'] + '\n')
	    f.write('Om =' + tipsy.paramfile['dOmega0'] + '\n')
	    f.write('# For GADGET2, you may need to specify conversion parameters. \n# Rockstar"s internal units are Mpc/h (lengths) and Msun/h (masses) \n')                              
	    f.write(fileformat + '_MASS_CONVERSION   = ' + str(dmsol*tipsy.h) + '\n')
	    f.write(fileformat + '_LENGTH_CONVERSION = '  + str(dkpc*tipsy.h/1e3) + '\n')
	    f.write(fileformat + '_VELOCITY_CONVERSION = ' + str(tipsy.velunit) + '\n')
	    f.write('BOX_SIZE = ' + str(dkpc*tipsy.h/1e3) + '\n')
	    f.write('#For ascii files, the file format is assumed to be: \n# X Y Z VX VY VZ ID \n')
	    f.write('#For non-periodic boundary conditions only: \n#PERIODIC=0 \n')                    
	    f.write('FULL_PARTICLE_CHUNKS = ' + str(ncorespernode*nnodes)  + '  # Should be the same as NUM_WRITERS above to save all particles \n')
	    f.write('PARALLEL_IO_SERVER_INTERFACE = "' + ServerInterface + '"\n')
	    f.write('MASS_DEFINITION  = "' + massdef + '"\n')
	    if massdef2: f.write('MASS_DEFINITION2 = "' + massdef2+ '"\n')
	    f.write('SUPPRESS_GALAXIES = 1 #Change to 0 to print out galaxies separately from halos (if there are any doubts about halo-galaxy assignment)\n')
	    f.write('NON_DM_METRIC_SCALING = 10 #Change to higher values to make the algorithm weight position space more than velocity space\n')
	    f.write('DENSITY_MERGE_THRESH = 1e22 #Change to higher values to make the algorithm split galaxies into more pieces.  Best to change at least a factor of 1e3 at a time in order to see any significant differences.\n')
	    f.close()


def mainsubmissionscript(walltime = '24:00:00', email = 'l.sonofanders@gmail.com', machine='stampede', nnodes=1, ncorespernode=32, queue='largemem', rockstardir='/home1/02575/lmanders/code/Rockstar-Galaxies/', basedir='.'):
    snapfiles = glob.glob('snaps*.txt')
    nsnapfiles = len(snapfiles)
    sbatchname = findtipsy.find(basedir=basedir)[0].split('.')[0]
    for ii in range(nsnapfiles):
	    configf = 'rockstar.submit.'+str(ii+1)+'.cfg'
	    snapsf = open('snaps'+str(ii+1)+'.txt','r')
	    snaps = snapsf.readlines()
	    if (machine == 'pleiades') or (machine == 'bluewaters'):
	        filename = 'rockstar.'+str(ii+1)+'.qsub'
	        f = open(filename, 'w')
	
	        f.write('#!/bin/bash \n')
	        f.write('#PBS -N ' + sbatchname + '.'+str(ii+1)+'.rock \n')
	        if machine == 'pleiades': f.write('#PBS -lselect=' + str(nnodes) + ':ncpus='+str(ncorespernode)+':mpiprocs=1'+ '\n')
	        if machine == 'bluewaters':f.write('#PBS -lnodes=' + str(nnodes) + ':ppn='+str(ncorespernode)+'\n')
	        f.write('#PBS -m be \n')
	        f.write('#PBS -M ' + email +' \n')
	        f.write('#PBS -q ' + queue + ' \n')
	        f.write('#PBS -l walltime=' + walltime + ' \n')
	        
	        f.write('cd $PBS_O_WORKDIR \n')
	        f.write('rm auto-rockstar.cfg \n')
	        f.write('ulimit -c unlimited \n')
	
	        if machine=='bluewaters': prefix = 'aprun -n ' + str(nnodes) + ' -N 1 -d 32 '
	        else: prefix = ''
	    
	        f.write(rockstardir + 'rockstar-galaxies -c '+configf+' & \n')
	        f.write("perl -e 'sleep 1 while (!(-e "+'"' + "auto-rockstar.cfg"+'"' + "))' \n")
	        f.write(prefix + rockstardir + 'rockstar-galaxies -c auto-rockstar.cfg \n')
	
	    if machine == 'stampede':
	        filename = 'rockstar.'+str(ii+1)+'.sbatch'
	        f = open(filename, 'w')
	
	        f.write('#!/bin/bash \n')
	        f.write('#SBATCH -J ' + sbatchname + ' \n')
	        f.write('#SBATCH -n ' + str(nnodes) + ' \n')
	        f.write('#SBATCH -N ' + str(nnodes) + ' \n')
	        f.write('#SBATCH -o ' + sbatchname + '.'+str(ii+1)+'.rockstar.o%j \n')
	        f.write('#SBATCH -p ' + queue + ' \n')
	        f.write('#SBATCH -t ' + walltime + ' \n')
	        f.write('#SBATCH --mail-user=l.sonofanders@gmail.com \n')
	        f.write('#SBATCH --mail-type=ALL \n')
	        f.write('#SBATCH -A TG-MCA94P018 \n')
	        f.write('## -n: total tasks \n')
	        f.write('## -N: nodes \n')
	        
	        f.write('cd $SLURM_SUBMIT_DIR \n')
	        f.write('rm auto-rockstar.cfg \n')
	        f.write('ulimit -c unlimited \n')
	
	        f.write(rockstardir + 'rockstar-galaxies -c '+configf+' & \n')
	        f.write("perl -e 'sleep 1 while (!(-e "+'"' + "auto-rockstar.cfg"+'"' + "))' \n")
	        f.write('ibrun ' + rockstardir + 'rockstar-galaxies -c auto-rockstar.cfg \n')

	    if machine == 'interactive':
	        filename = 'rockstar.'+str(ii)+'.sh'
	        f = open(filename, 'w')
	
	        f.write('#/bin/sh \n')
	        f.write('rm auto-rockstar.cfg \n')
	        f.write(rockstardir + 'rockstar-galaxies -c '+configf+' & \n')
	        f.write("perl -e 'sleep 1 while (!(-e "+'"' + "auto-rockstar.cfg"+'"' + "))' \n")
	        f.write(rockstardir + 'rockstar-galaxies -c auto-rockstar.cfg \n')
	    for jj in range(len(snaps)):
		f.write("mv out_"+str(jj)+".list out_"+snaps[jj].strip('\n')+'\n')
	    f.close()


def postsubmissionscript(email = 'l.sonofanders@gmail.com', machine = 'stampede', queue = 'largemem', rockstardir='/home1/02575/lmanders/code/Rockstar-Galaxies', ncorespernode=32, walltime='24:00:00', nnodes=1, fileformat='TIPSY', basedir='.',cleanup=True,nmin=0):
    snapfiles = glob.glob('snaps*.txt')
    nsnapfiles = len(snapfiles)
    tipsyfile = findtipsy.find(basedir=basedir)[0]
    iordfilepre = ('.').join(tipsyfile.split('.')[:-1])
    sbatchname = findtipsy.find(basedir=basedir)[0].split('.')[0]
    
    sim = nptipsyreader.Tipsy(tipsyfile)
    sim._read_param()
    boxsize = str(float(sim.paramfile['dKpcUnit'])/1000.*sim.h)
    
    #outfiles = glob.glob('out_*.list')
    simcnt = 0
    for ii in range(nsnapfiles):
	    snapsf = open('snaps'+str(ii+1)+'.txt')
	    snaps = [line.split('\n')[0] for line in snapsf]
	    snapsf.close()
	    
	    genstatexecline = []
	    
	    if machine == 'stampede':
	        f = open('rockstar.post.'+str(ii+1)+'.sbatch', 'w')
	
	        f.write('#!/bin/bash \n')
	        f.write('#SBATCH -J' + sbatchname +'.rockp \n')
	        f.write('#SBATCH -n 1 \n')
	        f.write('#SBATCH -N 1 \n')
	        f.write('#SBATCH -o ' + iordfilepre + '.rockstar.o%j \n')
	        f.write('#SBATCH -p ' + queue + ' \n')
	        f.write('#SBATCH -t ' + walltime + ' \n')
	        f.write('#SBATCH --mail-suers=' + email + '\n')
	        f.write('#SBATCH --mail-type=ALL \n')
	        f.write('#SBATCH -A TG-MCA94P018 \n')
	        f.write('cd $SLURM_SUBMIT_DIR \n')
	        f.write('rm auto-rockstar.cfg \n')
	        f.write('ulimit -c unlimited \n')
	    if (machine == 'pleiades') or (machine == 'bluewaters'):
        	f = open('rockstar.post.'+str(ii+1)+'.qsub', 'w')
	
	        f.write('#!/bin/bash \n')
	        f.write('#PBS -N '+sbatchname+'.'+str(ii+1)+'rockp \n')
	        if machine == 'pleiades':f.write('#PBS -lselect=1:ncpus='+str(ncorespernode)+':mpiprocs=1 \n')
	        if machine == 'bluewaters':f.write('#PBS -lnodes=1:ppn='+str(ncorespernode)+' \n')
	        f.write('#PBS -q ' + queue + ' \n')
	        f.write('#PBS -l walltime=' + walltime + ' \n')
	        f.write('#PBS -m be \n')
	        f.write('#PBS -M ' + email + '\n')
	        f.write('cd $PBS_O_WORKDIR \n')
	        f.write('ulimit -c unlimited \n')
	    if (machine == 'interactive'):
	        f = open('rockstar.post.'+str(ii+1)+'.sh', 'w')
	        f.write('#/bin/sh \n')
	
	    for i in range(len(snaps)):
	        parentexecline = (rockstardir + 'util/find_parents out_'+ snaps[i] + '.list ' + boxsize + ' > out_'+ snaps[i] + '.parents \n' )
	        f.write(parentexecline)
	        if fileformat == 'TIPSY': iordf = iordfilepre + '.' + snaps[i] + '.iord'
	        if fileformat == 'NCHILADA': iordf = iordfilepre + '.' + snaps[i]
	        genstatexecline.append(rockstardir + 'examples/gen_pynbody_stats out_' + snaps[i] + '.parents ' + basedir + '/' + iordf + ' '+str(nmin)+' halos_' + snaps[i] + '.*.particles \n')
	        
	        
	    for i in range(len(snaps)):
	        f.write("perl -e 'sleep 1 while (!(-e " + '"' + "out_" + snaps[i] + ".parents"+'"'+"))'" + "\n")
	        f.write(genstatexecline[i])
	    for i in range(len(snaps)):
	        f.write("perl -e 'sleep 1 while (!(-e " + '"' + "out_" + snaps[i] + ".grp"+'"'+"))'" + "\n")
	        f.write("mv out_" + snaps[i] + ".grp "  + iordfilepre+'.'+snaps[i]+".rockstar.grp \n")
	        f.write("perl -e 'sleep 1 while (!(-e " + '"' + "out_" + snaps[i] + ".stat"+'"'+"))'" + "\n")
	        f.write("mv out_" + snaps[i] + ".stat " + iordfilepre+'.'+snaps[i]+".rockstar.stat \n")
		f.write("perl -e 'sleep 1 while (!(-e " + '"' + "out_" + snaps[i] + ".halos"+'"'+"))'" + "\n")
		f.write("mv out_" + snaps[i] + ".halos " + iordfilepre+'.'+snaps[i]+".rockstar.halos \n")
		f.write("perl -e 'sleep 1 while (!(-e " + '"' + "out_" + snaps[i] + ".particles"+'"'+"))'" + "\n")
		f.write("mv out_" + snaps[i] + ".particles " + iordfilepre+'.'+snaps[i]+".rockstar.halo_particles \n")
	    if cleanup==True:
		f.write('rm halos_*.particles \n')
		f.write('mv halos_* rockstarfiles\n')
	    f.close()
	    #    os.system(parentexecline)
	    #    os.system(genstatexecline)
