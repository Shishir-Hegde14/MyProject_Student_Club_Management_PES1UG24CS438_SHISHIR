from pathlib import Path
import math
from reportlab.pdfgen import canvas
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
W,H=1100,760


def text(c,x,y,content,size=12,center=False):
    c.setFont('Helvetica',size)
    for i,line in enumerate(content.split('\n')):
        (c.drawCentredString if center else c.drawString)(x,H-y-i*(size+4),line)


def rect(c,x,y,w,h):
    c.rect(x,H-y-h,w,h,fill=0)


def line(c,x1,y1,x2,y2,dashed=False,arrow=False):
    c.setDash(4,3) if dashed else c.setDash()
    c.line(x1,H-y1,x2,H-y2)
    c.setDash()
    if arrow:
        angle=math.atan2(y2-y1,x2-x1)
        for d in (-.45,.45):
            c.line(x2,H-y2,x2-10*math.cos(angle+d),H-y2+10*math.sin(angle+d))


def title(c,heading):
    text(c,W/2,30,heading,18,True)
    text(c,W/2,53,'Shishir Hegde | PES1UG24CS438 | Section 5H',11,True)


def component(c,x,y,w,h,label):
    rect(c,x,y,w,h)
    text(c,x+w/2,y+23,'<<component>>',11,True)
    text(c,x+w/2,y+46,label,12,True)


def connector(c,x,y1,y2,label):
    rect(c,x-3,y1-3,6,6)
    mid=(y1+y2)/2
    line(c,x,y1+3,x,mid-8)
    c.arc(x-8,H-mid-8,x+8,H-mid+8,startAng=0,extent=180)
    c.circle(x,H-mid,5,fill=0)
    line(c,x,mid+5,x,y2)
    rect(c,x-3,y2-3,6,6)
    text(c,x+13,mid+4,label,10)


def save(c,path):
    c.save()
    doc=pdfium.PdfDocument(str(path))
    doc[0].render(scale=1.8).to_pil().save(path.with_suffix('.png'))
    doc.close()


def architecture():
    path=ROOT/'2-Architecture/component-diagram.pdf'
    c=canvas.Canvas(str(path),pagesize=(W,H))
    title(c,'Student Club Portal Component Diagram')
    text(c,35,88,'Presentation layer',12)
    component(c,45,105,1010,65,'Portal Web UI')
    text(c,35,270,'Business layer',12)
    centers=[140,345,550,755,960]
    names=['Authentication','Event and Budget','Ticket Service','Check-in Service','Dashboard Service']
    interfaces=['IAuth','IEventBudget','ITicket','ICheckIn','IStatus']
    for x,name,interface in zip(centers,names,interfaces):
        component(c,x-90,290,180,80,name)
        connector(c,x,170,290,interface)
        connector(c,x,370,495,'IDataStore')
    text(c,35,476,'Data layer',12)
    component(c,45,495,1010,70,'SQLite Repository')
    text(c,550,590,'Users | Clubs | Events | Budget items | Approvals | Tickets',11,True)
    text(c,45,625,'Interface key',12)
    text(c,45,648,'Circle = provided interface     Semicircle = required interface     Small square = port',11)
    text(c,45,671,'UI to services: HTTP forms / JSON endpoints. Services to repository: parameterised SQL.',11)
    text(c,45,694,'The consumer is above the provider. Each ball and socket pair is an assembly connector.',11)
    text(c,45,717,'Logical components share one Flask application. There are no separately deployed microservices.',11)
    save(c,path)


def actor(c,x,y,name):
    c.circle(x,H-y,9,fill=0)
    line(c,x,y+9,x,y+38)
    line(c,x-18,y+21,x+18,y+21)
    line(c,x,y+38,x-16,y+61)
    line(c,x,y+38,x+16,y+61)
    text(c,x,y+81,name,12,True)


def oval(c,x,y,w,h,label):
    c.ellipse(x,H-y-h,x+w,H-y,fill=0)
    lines=label.split('\n')
    text(c,x+w/2,y+h/2-(len(lines)-1)*7+4,label,11,True)


def use_cases():
    path=ROOT/'1-Requirements-Engineering/use-case-diagram.pdf'
    c=canvas.Canvas(str(path),pagesize=(W,H))
    title(c,'Student Club Portal Use Case Diagram')
    rect(c,210,85,680,575)
    text(c,550,109,'Student Club Event and Budget Portal',14,True)
    actor(c,95,170,'Club Lead')
    actor(c,95,450,'Student')
    actor(c,995,220,'Approver')
    actor(c,995,520,'Check-in Staff')
    oval(c,250,140,205,55,'Create or edit proposal')
    oval(c,250,240,205,55,'Request budget')
    oval(c,610,240,225,55,'Validate allocation')
    oval(c,250,345,205,55,'Track event status')
    oval(c,610,140,225,55,'Review budget request')
    oval(c,610,345,225,55,'Reject budget request')
    oval(c,250,455,205,55,'Register for event')
    oval(c,610,455,225,55,'Generate QR ticket')
    oval(c,250,560,205,55,'Validate ticket')
    oval(c,610,560,225,55,'Scan ticket')
    for y in (167,267,372): line(c,113,191,250,y)
    line(c,113,472,250,482)
    line(c,977,241,835,167)
    line(c,977,541,835,587)
    line(c,455,267,610,267,True,True)
    text(c,530,253,'<<include>>',10,True)
    line(c,455,482,610,482,True,True)
    text(c,530,468,'<<include>>',10,True)
    line(c,610,587,455,587,True,True)
    text(c,530,573,'<<include>>',10,True)
    line(c,835,372,870,372,True)
    line(c,870,372,870,167,True)
    line(c,870,167,835,167,True,True)
    text(c,855,414,'<<extend>>',10,True)
    text(c,755,432,'[decision is reject]',10,True)
    text(c,45,690,'Approver roles: Faculty Coordinator, Finance Officer and Dean, in that order.',11)
    text(c,45,713,'The original Lab 1 image is preserved in originals. This revised diagram adds the attendee and staff roles.',11)
    save(c,path)


if __name__=='__main__':
    architecture()
    use_cases()
