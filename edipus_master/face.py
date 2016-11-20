class Face:
    def __init__(self, cv_img, identity):
        self.cv_img = cv_img
        self.identity = identity

def checking_one_face(Faces):
    if (Faces is not None):
        l = Faces[0].identity
        for f in Faces:
            if (f.identity is not l):
                return False
        return True
def counting_faces(Faces):
    if (Faces is not None):
        owner = 0
        others = 0
        for f in Faces:
            if (f.identity is 1):
                owner += 1
            if (f.identity is 0):
                others += 1
        return (owner, others)