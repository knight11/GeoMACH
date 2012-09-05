from __future__ import division
import numpy, pylab, copy
import PUBS, PUBSlib


class PUBSexport(object):

    def __init__(self, model):
        self.model = model

    def write2Tec(self,filename):
        model = self.model
        f = open(filename+'.dat','w')
        f.write('title = "PUBSlib output"\n')
        f.write('variables = "x", "y", "z"\n')
        for surf in range(model.nsurf):
            ugroup = model.edge_group[abs(model.surf_edge[surf,0,0])-1]
            vgroup = model.edge_group[abs(model.surf_edge[surf,1,0])-1]
            nu = model.group_n[ugroup-1]
            nv = model.group_n[vgroup-1]      
            f.write('zone i='+str(nu)+', j='+str(nv)+', DATAPACKING=POINT\n')
            P = PUBSlib.getsurfacep(surf+1, model.nP, nu, nv, model.nsurf, model.nedge, model.nvert, model.surf_vert, model.surf_edge, model.surf_index_P, model.edge_index_P, model.P)
            for v in range(nv):
                for u in range(nu):
                    f.write(str(P[u,v,0]) + ' ' + str(P[u,v,1]) + ' ' + str(P[u,v,2]) + '\n')
        f.close()

    def write2TecC(self,filename):
        model = self.model
        f = open(filename+'.dat','w')
        f.write('title = "PUBSlib output"\n')
        f.write('variables = "x", "y", "z"\n')        
        f.write('zone i='+str(model.nC)+', DATAPACKING=POINT\n')
        for i in range(model.nC):
            f.write(str(model.C[i,0]) + ' ' + str(model.C[i,1]) + ' ' + str(model.C[i,2]) + '\n')
        f.close()

    def write2IGES(self, filename):
        model = self.model
        def getProps(surf):
            ugroup = model.edge_group[abs(model.surf_edge[surf,0,0])-1]
            vgroup = model.edge_group[abs(model.surf_edge[surf,1,0])-1]
            ku = model.group_k[ugroup-1]
            kv = model.group_k[vgroup-1]      
            mu = model.group_m[ugroup-1]
            mv = model.group_m[vgroup-1]      
            du = model.group_d[model.knot_index[ugroup-1,0]:model.knot_index[ugroup-1,1]]
            dv = model.group_d[model.knot_index[vgroup-1,0]:model.knot_index[vgroup-1,1]]
            return ku,kv,mu,mv,du,dv            

        def write(f, val, dirID, parID, field, last=False):
            if last:
                f.write('%20.12e;' %(val.real))
            else:
                f.write('%20.12e,' %(val.real))
            field += 1
            if field==3:
                field = 0
                f.write('%9i' %(dirID))
                f.write('P')
                f.write('%7i\n' %(parID))
                parID += 1
            return parID, field

        f = open(filename+'.igs','w')
        f.write('                                                                        S      1\n')
        f.write('1H,,1H;,4HSLOT,37H$1$DUA2:[IGESLIB.BDRAFT.B2I]SLOT.IGS;,                G      1\n')
        f.write('17HBravo3 BravoDRAFT,31HBravo3->IGES V3.002 (02-Oct-87),32,38,6,38,15,  G      2\n')
        f.write('4HSLOT,1.,1,4HINCH,8,0.08,13H871006.192927,1.E-06,6.,                   G      3\n')
        f.write('31HD. A. Harrod, Tel. 313/995-6333,24HAPPLICON - Ann Arbor, MI,4,0;     G      4\n')

        dirID = 1
        parID = 1    
        for surf in range(model.nsurf):
            ku,kv,mu,mv,du,dv = getProps(surf)
            numFields = 4 + du.shape[0] + dv.shape[0] + 4*mu*mv
            numLines = 2 + numpy.ceil(numFields/3.0)
            for val in [128, parID, 0, 0, 1, 0, 0, 0]:
                f.write('%8i' %(val))
            f.write('00000001')
            f.write('D')
            f.write('%7i\n' %(dirID))
            dirID += 1
            for val in [128, 0, 2, numLines, 0]:
                f.write('%8i' %(val))
            f.write('%32i' %(0))
            f.write('D')
            f.write('%7i\n' %(dirID))
            dirID += 1
            parID += numLines
        nDir = dirID - 1

        dirID = 1    
        parID = 1
        for surf in range(model.nsurf):
            ku,kv,mu,mv,du,dv = getProps(surf)

            for val in [128, mu-1, mv-1, ku-1, kv-1]:
                f.write('%12i,' %(val))
            f.write('%7i' %(dirID))   
            f.write('P')
            f.write('%7i\n' %(parID))
            parID += 1

            for val in [0, 0, 1, 0, 0]:
                f.write('%12i,' %(val))
            f.write('%7i' %(dirID))   
            f.write('P')
            f.write('%7i\n' %(parID))
            parID += 1

            field = 0
            for i in range(du.shape[0]):
                parID,field = write(f, du[i], dirID, parID, field)
            for i in range(dv.shape[0]):
                parID,field = write(f, dv[i], dirID, parID, field)
            for i in range(mu*mv):
                parID,field = write(f, 1.0, dirID, parID, field)
            for j in range(mv):
                for i in range(mu):
                    C = model.C[model.computeIndex(surf,i,j,1)]
                    for k in range(3):
                        parID,field = write(f, C[k].real, dirID, parID, field)
            parID,field = write(f, 0, dirID, parID, field)
            parID,field = write(f, 1, dirID, parID, field)
            parID,field = write(f, 0, dirID, parID, field)
            parID,field = write(f, 1, dirID, parID, field, last=True)
            if not field==0:
                for i in range(3-field):
                    f.write('%21s' %(' '))
                f.write('%9i' %(dirID))
                f.write('P')
                f.write('%7i\n' %(parID))
                parID += 1

            dirID += 2

        nPar = parID - 1

        f.write('S%7i' %(1))   
        f.write('G%7i' %(4))   
        f.write('D%7i' %(nDir))   
        f.write('P%7i' %(nPar))   
        f.write('%40s' %(' '))   
        f.write('T')
        f.write('%7i\n' %(1))       
        f.close()

    def write2EGADS(self,filename):
        model = self.model
        Ps = []
        for surf in range(model.nsurf):
            ugroup = model.edge_group[abs(model.surf_edge[surf,0,0])-1]
            vgroup = model.edge_group[abs(model.surf_edge[surf,1,0])-1]
            nu = model.group_n[ugroup-1]
            nv = model.group_n[vgroup-1]      
            P = PUBSlib.getsurfacep(surf+1, model.nP, nu, nv, model.nsurf, model.nedge, model.nvert, model.surf_vert, model.surf_edge, model.surf_index_P, model.edge_index_P, model.P)
            Ps.append(P[:,:,:])
            Ps.append(copy.copy(P[::-1,:,:]))
            Ps[-1][:,:,2] *= -1

        oml0 = PUBS.PUBS(Ps)

        file = open(filename+'.dat',"w")

        file.write(str(oml0.nvert)+'\n')
        file.write(str(oml0.nedge)+'\n')
        file.write(str(oml0.nsurf)+'\n')

        for i in range(oml0.nvert):
            file.write(str(oml0.C[i,0])+' ')
            file.write(str(oml0.C[i,1])+' ')
            file.write(str(oml0.C[i,2])+'\n')

        edgePtr = numpy.zeros((oml0.nedge,3),int)
        for i in range(oml0.nsurf):
            for u in range(2):
                for v in range(2):
                    edgePtr[abs(oml0.surf_edge[i,u,v])-1,:] = [i,u,v]
        ms = PUBSlib.getsurfacesizes(oml0.nsurf, oml0.nedge, oml0.ngroup, oml0.surf_edge, oml0.edge_group, oml0.group_m)
        for i in range(oml0.nedge):
            surf = edgePtr[i,0]
            edge0 = edgePtr[i,1]
            edge1 = edgePtr[i,2]
            if edge0==0:
                if edge1==0:
                    start = [0,0]
                    end = [1,0]
                else:
                    start = [0,1]
                    end = [1,1]
            else:
                if edge1==0:
                    start = [0,0]
                    end = [0,1]
                else:
                    start = [1,0]
                    end = [1,1]
            if oml0.surf_edge[surf,edge0,edge1] < 0:
                temp = start
                start = end
                end = temp
            file.write(str(oml0.surf_vert[surf,start[0],start[1]])+' ')
            file.write(str(oml0.surf_vert[surf,end[0],end[1]])+'\n')
            group = oml0.edge_group[i] - 1
            k = oml0.group_k[group]
            m = oml0.group_m[group]
            file.write(str(k)+' ')
            file.write(str(m)+'\n')
            d = oml0.group_d[oml0.knot_index[group,0]:oml0.knot_index[group,1]]
            for j in range(d.shape[0]):
                file.write(str(d[j])+' ')
            file.write('\n')
            C = PUBSlib.getsurfacep(surf+1, oml0.nC, ms[surf,0], ms[surf,1], oml0.nsurf, oml0.nedge, oml0.nvert, oml0.surf_vert, oml0.surf_edge, oml0.surf_index_C, oml0.edge_index_C, oml0.C)
            if edge0==0:
                if edge1==0:
                    edgeCs = copy.copy(C[:,0,:])
                else:
                    edgeCs = copy.copy(C[:,-1,:])
            else:
                if edge1==0:
                    edgeCs = copy.copy(C[0,:,:])
                else:
                    edgeCs = copy.copy(C[-1,:,:])
            if oml0.surf_edge[surf,edge0,edge1] < 0:
                edgeCs[:,:] = copy.copy(edgeCs[::-1,:])
            for j in range(edgeCs.shape[0]):
                file.write(str(edgeCs[j,0])+' ')
                file.write(str(edgeCs[j,1])+' ')
                file.write(str(edgeCs[j,2])+'\n')

        for i in range(oml0.nsurf):
            for u in range(2):
                for v in range(2):
                    file.write(str(oml0.surf_edge[i,u,v])+' ')
            file.write('\n')
            ugroup = oml0.edge_group[abs(oml0.surf_edge[i,0,0])-1] - 1
            vgroup = oml0.edge_group[abs(oml0.surf_edge[i,1,0])-1] - 1
            ku = oml0.group_k[ugroup]
            mu = oml0.group_m[ugroup]
            kv = oml0.group_k[vgroup]
            mv = oml0.group_m[vgroup]
            file.write(str(ku)+' ')
            file.write(str(mu)+' ')
            file.write(str(kv)+' ')
            file.write(str(mv)+' ')
            file.write('\n')    
            d = oml0.group_d[oml0.knot_index[ugroup,0]:oml0.knot_index[ugroup,1]]
            for j in range(d.shape[0]):
                file.write(str(d[j])+' ')
            file.write('\n') 
            d = oml0.group_d[oml0.knot_index[vgroup,0]:oml0.knot_index[vgroup,1]]
            for j in range(d.shape[0]):
                file.write(str(d[j])+' ')
            file.write('\n')
            C = PUBSlib.getsurfacep(i+1, oml0.nC, ms[i,0], ms[i,1], oml0.nsurf, oml0.nedge, oml0.nvert, oml0.surf_vert, oml0.surf_edge, oml0.surf_index_C, oml0.edge_index_C, oml0.C)
            for v in range(C.shape[1]):
                for u in range(C.shape[0]):
                    file.write(str(C[u,v,0])+' ')
                    file.write(str(C[u,v,1])+' ')
                    file.write(str(C[u,v,2])+'\n')

        file.close()
