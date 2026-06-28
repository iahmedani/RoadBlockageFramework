
# ACLED Codebook | ACLED

Methodology

# ACLED Codebook

As the ultimate guide on ACLED data, the codebook details our global data collection process and defines event types and actor categories.

## **Introduction**

ACLED collects reported information on the type, agents, location, date, and other characteristics of political violence events, demonstration events, and other select non-violent, politically-relevant developments in every country and territory in the world. ACLED focuses on tracking a range of violent and non-violent actions by or affecting political agents, including governments, rebels, militias, identity groups, political parties, external forces, rioters, protesters, and civilians. The full list of ACLED data columns is available in the [table below](https://acleddata.com/knowledge-base/codebook/#table-1).

ACLED concentrates on:

- Tracking rebel, militia, and government activity over time and space;
- Recording violent acts between and across non-state groups, including political and identity militias;
- Recording political violence by unnamed agents, as violent groups may remain unnamed for strategic reasons;
- Recording attacks on civilians by all violent political agents;
- Distinguishing between territorial transfers of military control from governments (and their affiliates) to non-state agents and vice versa;
- Collecting information on rioting and protesting; and
- Tracking non-violent strategic developments representing crucial junctures in periods of political violence (e.g. recruitment drives, peace talks, high-level arrests).

ACLED data are derived from a wide range of local, national, and international sources in over 75 languages. The information is collected by trained researchers worldwide. An updated overview of ACLED’s current country and time period coverage is available [here](https://acleddata.com/knowledge-base/country-time-period-coverage/).

ACLED data are coded in real time and published on a weekly basis following a multi-stage internal [review process](https://acleddata.com/knowledge-base/how-does-acled-code-and-review-data-to-ensure-quality/). Data can be downloaded through the [export tool](https://acleddata.com/data-export-tool/), [curated data files](https://www.acleddata.com/curated-data-files/) (which include regional data files and files for specific subsets like violence targeting civilians), or [API](https://apidocs.acleddata.com/ "(opens in a new window)") with a [free account](https://acleddata.com/register/). Further guides to ACLED’s methodology, coding decisions, and access system are available on the [ACLED Knowledge Base](https://acleddata.com/knowledge-base/).

## **ACLED Data Columns at a Glance**

_Table 1: Data Columns_

**Column name**

**Column description**

**Values**

_event\_id\_cnty_

A unique alphanumeric event identifier by number and country acronym. This identifier remains constant even when the event details are updated.

E.g., ETH9766

_event\_date_

The date on which the event took place. Recorded as year-month-day.

E.g., 2023-02-16

_year_

The year in which the event took place.

E.g., 2018

_time\_precision_

A numeric code between 1 and 3 indicating the level of precision of the date recorded for the event. The higher the number, the lower the precision.

1, 2, or 3; with 1 being the most precise.

_disorder\_type_

The disorder category an event belongs to.

Political violence, Demonstrations, or Strategic developments.

_event\_type_

The type of event; further specifies the nature of the event.

E.g., Battles
_For the full list of ACLED event types, see the_ [_ACLED Event Types table_](https://acleddata.com/knowledge-base/codebook/#event-types-table)_._

_sub\_event\_type_

A subcategory of the event type.

E.g., Armed clash
_For the full list of ACLED sub-event types, see the_ [_ACLED Event Types table_](https://acleddata.com/knowledge-base/codebook/#event-types-table)_._

_actor1_

One of two main actors involved in the event (does not necessarily indicate the [aggressor](https://acleddata.com/knowledge-base/can-it-be-assumed-that-actor-1-is-the-aggressor/)).

E.g., Rioters (Papua New Guinea)

_assoc\_actor\_1_

Actor(s) involved in the event alongside Actor 1 or actor designations that further identify Actor 1.

E.g., Labor Group (Spain); Women (Spain)
Can have multiple actors separated by a semicolon, or can be blank.

_inter1_

A text value indicating the type of Actor 1 (_for more, see the section_ [_Actor Names, Types, and ‘Inter’ Codes_](https://acleddata.com/knowledge-base/codebook/#actor-names-types-and-inter-codes)).

E.g., Rebel group

_actor2_

One of two main actors involved in the event (does not necessarily indicate the [target or victim](https://acleddata.com/knowledge-base/can-it-be-assumed-that-actor-1-is-the-aggressor/)).

E.g., Civilians (Kenya)
Can be blank.

_assoc\_actor\_2_

Actor(s) involved in the event alongside Actor 2 or actor designation further identifying ‘Actor 2.

E.g., Labor Group (Spain); Women (Spain)
Can have multiple actors separated by a semicolon, or can be blank.

_inter2_

A text value indicating the type of Actor 2 (_for more, see the section_ [_Actor Names, Types, and ‘Inter’ Codes_](https://acleddata.com/knowledge-base/codebook/#actor-names-types-and-inter-codes)).

E.g., State forces
Can be blank.

_interaction_

A text value based on a combination of Inter 1 and Inter 2 indicating the two actor types interacting in the event (_for more, see the section_ [_Actor Names, Types, and ‘Inter’ Codes_](https://acleddata.com/knowledge-base/codebook/#actor-names-types-and-inter-codes)).

E.g., Rebel group – Civilians

_civilian\_targeting_

This column indicates whether the event involved civilian targeting.

Either "Civilians targeted" or blank.

_iso_

A unique three-digit numeric code assigned to each country or territory according to [ISO 3166](https://www.iso.org/iso-3166-country-codes.html "(opens in a new window)").

E.g., 231 for Ethiopia

_region_

The region of the world where the event took place.

E.g., Eastern Africa

_country_

The country or territory in which the event took place.

E.g., Ethiopia

_admin1_

The largest sub-national administrative region in which the event took place.

E.g., Oromia

_admin2_

The second largest sub-national administrative region in which the event took place.

E.g., Arsi
Can be blank.

_admin3_

The third largest sub-national administrative region in which the event took place.

E.g., Merti
Can be blank.

_location_

The name of the location at which the event took place.

E.g., Abomsa

_latitude_

The latitude of the location in four decimal degrees notation (EPSG:4326).

E.g., 8.5907

_longitude_

The longitude of the location in four decimal degrees notation (EPSG:4326).

E.g., 39.8588

_geo\_precision_

A numeric code between 1 and 3 indicating the level of certainty of the location recorded for the event. The higher the number, the lower the precision.

1, 2, or 3; with 1 being the most precise.

_source_

The sources used to record the event. Separated by a semicolon.

E.g., Ansar Allah; Yemen Data Project

_source\_ scale_

An indication of the geographic closeness of the used sources to the event (_for more, see the section_ [_Source Scale_](https://acleddata.com/knowledge-base/codebook/#source-scale)).

E.g., Local partner-National

_notes_

A short description of the event.

E.g., On 16 February 2023, OLF-Shane abducted an unidentified number of civilians after stopping a vehicle in an area near Abomsa (Merti, Arsi, Oromia). The abductees were traveling from Adama to Abomsa, Arsi.

_fatalities_

The number of reported fatalities arising from an event. When there are conflicting reports, the most conservative estimate is recorded.

E.g., 3
No information on fatalities is recorded as 0 reported fatalities.

_tags_

Additional structured information about the event. Separated by a semicolon.

E.g., women targeted: politicians; sexual violence

_timestamp_

An automatically generated [Unix timestamp](https://www.unixtimestamp.com/ "(opens in a new window)") that represents the exact date and time an event was uploaded to the ACLED API.

E.g., 1676909320

## **ACLED events**

ACLED collects and records reported information on political violence, demonstrations (rioting and protesting), and other select non-violent, politically important events. It aims to capture the modes, frequency, and intensity of political violence and demonstrations.

Political violence is defined as the use of force by a group with a political purpose or motivation, or with distinct political effects.[1](#footnote1 "ACLED includes organized criminal violence as political violence when it challenges safety, security, and territorial control within a state. For more on this, see the ACLED Gang Methodology.") A political violence event is a single altercation where force is used by one or more groups toward a political end. A demonstration event is an in-person public gathering of three or more people advocating for a shared cause. Other select non-violent instances of politically significant developments are also included in the dataset to capture the potential precursors or critical junctures of a violent conflict.

ACLED has developed a system that defines political disorder by its constituent events. It begins with robust and broad definitions of political violence and demonstrations (_more below_) and limits the taxonomy of political disorder to event types and sub-event types. This taxonomy allows users to compare trends of political disorder across countries and time periods. ACLED does not predefine broader aggregate categories of events, like wars, conflicts, operations, campaigns, or movements.[2](#footnote2 "ACLED also does not categorize clusters or campaigns of events into categories of state or non-state operations, terrorism, insurgency, etc. This is because political violence, demonstrations, conflict, and disorder are aggregations of multiple actors, attacks, goals, etc. Classifying events into parts of a civil war, livelihood, religious, or election conflict (to name a few common versions) is often a reductive choice, leaving out the complex ways conflict creates multiple scales of violence and intended outcomes within a territory.") These analytical decisions are left to the user.

ACLED allows users to filter data based on the type of event, type of actor, type of interaction, actors, location, or time period. ACLED does not dictate nor frame aggregations of conflict events, but allows users to determine how to define and explore frames. In this way, the dataset is designed to provide a comprehensive overview of political disorder around the world.

### **Event types and sub-event types**

The fundamental unit of observation in ACLED is the event. Events involve designated actors — e.g., a named rebel group, a militia, or state forces.[3](#footnote3 "With the sole exception of Unidentified Armed Group and generic categories including Rioters, Protesters, and Civilians.") They occur at a specific named location (identified by name and geographic coordinates) and on a specific day. Researchers work to ensure that the most specific possible location and time are recorded. ACLED currently records six event types and 25 sub-event types, both violent and non-violent. Sub-event types are also categorized by three overarching disorder types to facilitate analysis: Political violence, Demonstrations, and Strategic developments.

_Table 2: ACLED event types, sub-event types, and disorder types_

**Event type**

**Sub-event type**

**Disorder type**

**Battles**

_Government regains territory_

**Political violence**

_Non-state actor overtakes territory_

_Armed clash_

**Protests**

_Excessive force against protesters_

**Political violence; Demonstrations**

_Protest with intervention_

**Demonstrations**

_Peaceful protest_

**Riots**

_Violent demonstration_

_Mob violence_

**Political violence**

**Explosions/Remote violence**

_Chemical weapon_

_Air/drone strike_

_Suicide bomb_

_Shelling/artillery/missile attack_

_Remote explosive/landmine/IED_

_Grenade_

**Violence against civilians**

_Sexual violence_

_Attack_

_Abduction/forced disappearance_

**Strategic developments**

_Agreement_

**Strategic developments**

_Arrests_

_Change to group/activity_

_Disrupted weapons use_

_Headquarters or base established_

_Looting/property destruction_

_Non-violent transfer of territory_

_Other_

Both event types and sub-event types are hierarchical to accommodate concurrent tactics within the same event, to avoid double-counting (_for more, see the section_ [_Event Aggregation_](https://acleddata.com/knowledge-base/codebook/#event-aggregation)). This means that an airstrike (individually recorded as an Explosions/Remote violence event) occurring within the same context as a ground battle would be recorded as one Battles event. Likewise, an attack on a civilian (individually recorded as a Violence against civilians event) occurring within the same context as a remote explosive detonation (individually recorded as an Explosions/Remote violence event) would be recorded as one Explosions/Remote violence event. A similar structure holds for sub-event types. Ground shelling occurring simultaneously as an airstrike would be recorded as an Air/drone strike event, as it is higher on the hierarchy than the Shelling/artillery/missile attack sub-event type. Likewise, a civilian abducted and then killed would be recorded with the Attack sub-event type because it is higher on the hierarchy than the Abduction/forced disappearance sub-event type. The event types and sub-event types noted in _Table 2_ above are presented in hierarchical order. It is important to keep these distinctions in mind when interpreting and drawing conclusions from the data.

### **Battles**

ACLED defines a Battles event as a violent interaction between two organized armed groups at a particular time and location. Battles can occur between armed and organized state, non-state, and external groups, and in any combination thereof. _There is no fatality minimum necessary for inclusion._ Civilians can be harmed in the course of larger Battles events if they are caught in the crossfire, for example, or affected by strikes on military targets, which is commonly referred to as "collateral damage" (_for more, see_ [_Indirect Killing of Civilians_](https://acleddata.com/knowledge-base/indirect-killing-of-civilians/)). When civilians are harmed in a Battles event, they are not recorded as an Associated Actor, the event is not marked in the Civilian targeting column (_for more, see_ [_Civilian targeting_](https://acleddata.com/knowledge-base/codebook/#civilian-targeting)), nor is a separate civilian-specific event recorded. If any civilian fatalities are reported as part of a battle, they are aggregated in the ‘Fatalities’ column for the Battles event, and they are described in the Notes column.

The specific elements of the definition of a Battles event are as follows:

1. Violent interaction: The exchange of armed force, or the use of armed force at close distance, between armed groups capable of inflicting harm upon the opposing side.
2. Organized armed groups: Collective actors assumed to be operating cohesively around an agenda, identity, or political purpose, using weapons to inflict harm. These groups frequently have a designated name and stated agenda.

The Battles event type may include: ground clashes between different armed groups, ground clashes between armed groups supported by artillery fire or airstrikes, ambushes of on-duty soldiers or armed militants, exchanges of artillery fire, ground attacks against military or militant positions, air attacks where ground forces are able to effectively fire on the aircraft, and air-to-air combat.

The following sub-event types are categorized under the Battles event type and are designated according to whether the battle does or does not result in a territorial exchange: Armed clash, Government regains territory, and Non-state actor overtakes territory.

Cases where territory is regained or overtaken without resistance or armed interaction are not recorded as Battles events. Instead, they are recorded as Non-violent transfer of territory under the Strategic developments event type _(more below)_.

_**Government regains territory**_

This sub-event type is used when government forces or their affiliates that are fighting against competing state forces or against a non-state group regain control of a location through armed interaction. This sub-event type is only recorded for the re-establishment of government control and not for cases where competing non-state actors exchange control. Short-lived and/or small-scale territorial exchanges that do not last for more than one day are recorded as ‘Armed clash’.

_**Non-state actor overtakes territory**_

This sub-event type is used when a non-state actor (excluding those operating directly on behalf of the government) or a foreign state actor, through armed interaction, captures territory from an opposing government or non-state actor; as a result, they are regarded as having a monopoly of force within that territory. Short-lived and/or small-scale territorial exchanges that do not last for more than one day are recorded as Armed clash events. In cases where non-state forces fight with opposing actors in a location many times before gaining control, only the final territorial acquisition is recorded as Non-state actor overtakes territory. All other battles in that location are recorded as Armed clash.

_**Armed clash**_

This sub-event type is used when armed, organized groups engage in a battle, and no reports indicate a significant change in territorial control _(as described above)_.

### **Protests**

A Protests event is defined as an in-person public demonstration of three or more participants in which the participants do not engage in violence, though violence may be used against them. Events include individuals and groups who peacefully demonstrate against a political entity, government institution, policy, group, tradition, business, or other private institution. The following are not recorded as Protests events: symbolic public acts such as displays of flags or public prayers (unless they are accompanied by a demonstration); legislative protests, such as parliamentary walkouts or members of parliaments staying silent; strikes (unless they are accompanied by a demonstration); and individual acts such as self-harm actions like individual immolations or hunger strikes.

Protesters are noted by generic actor names: **Protesters (Country)**. If they are representing a group, the name of that group is recorded in the corresponding Associated Actor column.

The following sub-event types are associated with the Protests event type: Peaceful protest, Protest with intervention, and Excessive force against protesters.

_**Excessive force against protesters**_

This sub-event type is used when individuals are engaged in a peaceful protest and are targeted with lethal violence or violence resulting in serious injuries (e.g., requiring hospitalization). This includes situations where remote explosives, such as IEDs, are used to target protesters, as well as situations where non-state actors, such as rebel groups, target protesters.

_**Protest with intervention**_

This sub-event type is used when individuals are engaged in a peaceful protest during which there is a physical attempt to disperse or suppress the protest without serious/lethal injuries or the targeting of protesters with lethal weapons reported. This sub-event type also covers any instance where armed groups or rioters interact with peaceful protesters without resulting in serious/lethal injuries, as well as cases where protesters are arrested.[4](#footnote4 "Dispersal orders or citations, in the absence of reports of physical action to detain or remove protesters, are not captured under this sub-event type; if protesters are only issued citations, the event would be coded as a Peaceful protest.")

_**Peaceful protest**_

This sub-event type is used when demonstrators gather for a protest and do not engage in violence or other forms of rioting activity, such as property destruction, and are not met with any sort of force or intervention.

### **Riots**

Riots are violent events where demonstrators or mobs of three or more engage in violent or destructive acts, including but not limited to physical fights, rock throwing, property destruction, etc. They may engage individuals, property, businesses, other rioting groups, or armed actors. Rioters are noted by generic actor names: **Rioters (Country)**. If rioters are affiliated with a specific group — which may or may not be armed — or identity group, that group is recorded in the respective Associated Actor column. Riots may begin as peaceful protests, or a mob may have the intention to engage in violence from the outset. Riots events where civilians are the main or only target will be tagged with “Civilians targeted” in the Civilian targeting column.

The following sub-event types are associated with the Riots event type: Violent demonstration and Mob violence.

_**Violent demonstration**_

This sub-event type is used when demonstrators engage in violence and/or destructive activity. Examples include physical clashes with other demonstrators or government forces; vandalism; and road-blocking using barricades, burning tires, or other material. The coding of an event as a Violent demonstration does not necessarily indicate that demonstrators initiated the violence and/or destructive actions, nor does the order of the actors coded necessarily indicate which side of a two- or multi-sided counter-demonstration initiated the violence and/or destructive activity.

_**Mob violence**_

This sub-event type is used when rioters violently interact with other rioters, civilians or their property, or armed groups outside of demonstration contexts. A mob is considered a crowd of people that is disorderly and has the intention to cause harm or disruption through violence or property destruction. Note that this type of violence can also include spontaneous vigilante mobs clashing with other armed groups or attacking civilians. While a Mob violence event often involves unarmed or crudely armed rioters, on rare occasions, it can involve violence by people associated with organized groups and/or using more sophisticated weapons, such as firearms.

### **Explosions/Remote violence**

ACLED defines Explosions/Remote violence events as incidents in which one side uses weapon types that, by their nature, are at range and widely destructive. The weapons used in Explosions/Remote violence events are explosive devices, including but not limited to: bombs, grenades, IEDs, artillery fire or shelling, missile attacks, air or drone strikes, and other widely destructive heavy weapons or chemical weapons. Suicide attacks using explosives also fall under this category. When an ‘Explosions/Remote violence event is reported in the context of an ongoing battle, it is merged and recorded as a single Battles event. Explosions/Remote violence can be used against armed agents as well as civilians. Explosions/Remote violence events where civilians are the main or only target will be tagged with “Civilians targeted” in the Civilian targeting column.

The following sub-event types are associated with the ‘Explosions/Remote violence’ event type: Chemical weapon, Air/drone strike, Suicide bomb, ‘Shelling/artillery/missile attack, Remote explosive/landmine/IED, and Grenade.

_**Chemical weapon**_

This sub-event type captures the use of chemical weapons in warfare in the absence of any other engagement. ACLED considers chemical weapons as all substances listed as Schedule 1 of the Chemical Weapons Convention, including sarin gas, mustard gas, chlorine gas, and anthrax. Napalm and white phosphorus, as well as less-lethal crowd control substances — such as tear gas — are not considered chemical weapons within this sub-event type.

_**Air/drone strike**_

This sub-event type is used when air or drone strikes take place in the absence of any other engagement. Please note that any air-to-ground attacks fall under this sub-event type, including attacks by helicopters that do not involve exchanges of fire with forces on the ground.

_**Suicide bomb**_

This sub-event type is used when a suicide bombing occurs in the absence of an armed clash, such as an exchange of small arms fire with other armed groups. It also includes suicide vehicle-borne IED (SVBIED) attacks. Note that the suicide bomber is included in the total number of reported fatalities coded for such events.

_**Shelling/artillery/missile attack**_

This sub-event type captures the use of long-range artillery, missile systems, or other heavy weapons platforms in the absence of any other engagement. When two armed groups exchange long-range fire, it is recorded as an Armed clash. Shelling/artillery/missile attack events include attacks described as shelling, the use of artillery and cannons, mortars, guided missiles, rockets, grenade launchers, and other heavy weapons platforms. Crewed aircraft shot down by long-range systems fall under this sub-event type. Uncrewed armed drones that are shot down, however, are recorded as interceptions under Disrupted weapons use because people are not targeted (_see_ [_below_](https://acleddata.com/knowledge-base/codebook/#disrupted-weapon-use)). Similarly, an interception of a missile strike itself (such as by the Iron Dome in Israel) is also recorded as Disrupted weapons use.

_**Remote explosive/landmine/IED**_

This sub-event type is used when remotely- or victim-activated devices are detonated in the absence of any other engagement. Examples include landmines, IEDs — whether alone or attached to a vehicle, or any other sort of remotely detonated or triggered explosive. Unexploded ordnances (UXO) also fall under this category.

SVBIEDs are recorded as Suicide bomb events (_see_ [_above_](https://acleddata.com/knowledge-base/codebook/#suicide-bomb)), while the safe defusal of an explosive or its accidental detonation by the actor who planted it (with no other casualties reported) is recorded under Disrupted weapons use (_see_ [_below_](https://acleddata.com/knowledge-base/codebook/#disrupted-weapon-use)).

_**Grenade**_

This sub-event type captures the use of a grenade or any other similarly hand-thrown explosive, such as an IED that is thrown, in the absence of any other engagement. Events involving so-called "crude bombs" (such as Molotov cocktails, firecrackers, cherry bombs, petrol bombs, etc.) as well as "stun grenades" are not recorded in this category, but are included under either Riots or Strategic developments depending on the context in which they occurred.

### **Violence against civilians**

ACLED defines Violence against civilians as violent events where an organized armed group inflicts violence upon unarmed non-combatants. By definition, civilians are unarmed and cannot engage in political violence. Therefore, the violence is understood to be asymmetric as the perpetrator is assumed to be the only actor capable of using violence in the event. The perpetrators of such acts include state forces and their affiliates, rebels, militias, and external/other forces.

In cases where the identity and actions of the targets are in question (e.g., the target may be employed as a police officer), ACLED determines that if a person is harmed or killed while unarmed and unable to either act defensively or counter-attack, this is an act of Violence against civilians. This includes extrajudicial killings of detained combatants or unarmed prisoners of war.   

Violence against civilians also includes attempts at inflicting harm (e.g., beating, shooting, torture, rape, mutilation, etc.) or forcibly disappearing (e.g., kidnapping and disappearances) civilian actors. Note that the Violence against civilians event type exclusively captures violence targeting civilians that does not occur concurrently with other forms of violence — such as rioting – that are coded higher in the ACLED event type hierarchy. To get a full list of events in the ACLED dataset where civilians were the main or only target of violence, users can filter on the Civilian targeting column (_for more, see_ [_Civilian targeting_](https://acleddata.com/knowledge-base/codebook/#civilian-targeting)).

The following sub-event types are associated with the Violence against civilians event type: Sexual violence, Attack, and Abduction/forced disappearance.

_**Sexual violence**_

This sub-event type is used when any individual is targeted with sexual violence. Sexual violence is defined largely as an action that inflicts harm of a sexual nature. This means that it is not limited to solely penetrative rape, but also includes actions like public stripping, sexual torture, etc. Given the gendered nature of sexual violence, the gender identities of the victims — i.e., **Women (Country)**, **Men (Country)**, and **LGBTQ+ (Country)**, or a combination thereof — are recorded in the Associated Actor column for these events when reported. Note that it is possible for sexual violence to occur within other event types such as Battles and Riots _(for more, see_ [_Sexual Violence in the ACLED Dataset_](https://acleddata.com/knowledge-base/how-is-sexual-violence-coded-in-acled-data/)_)._

_**Attack**_

This sub-event type is used when civilians are targeted with violence by an organized armed actor outside the context of other forms of violence coded higher in the ACLED event type hierarchy. Attacks of a sexual nature are recorded as Sexual violence (_see_ [_above_](https://acleddata.com/knowledge-base/codebook/#sexual-violence)). Violence by law enforcement that constitutes severe government overreach is also recorded as an Attack event.

_**Abduction/forced disappearance**_

This sub-event type is used when an actor engages in the abduction or forced disappearance of civilians, without reports of further violence. If fatalities or serious injuries are reported during the abduction or forced disappearance, the event is recorded as an Attack event instead. If such violence is reported in later periods during captivity, this is recorded as an additional Attack event. Note that multiple people can be abducted in a single Abduction/forced disappearance event.

Arrests by non-state groups and extrajudicial detentions by state forces are considered ‘Abduction/forced disappearance’. Arrests conducted by state forces within the standard judicial process are, however, considered ‘Arrests’ _(see_ [_below_](https://acleddata.com/knowledge-base/codebook/#arrests)_)._[5](#footnote5 "In rare cases where non-state groups are able to maintain some level of judicial/penal system, they are also considered able to engage in Arrests, and these actions are not recorded as Abduction/forced disappearance and are instead recorded under the Arrests sub-event type.")

### **Strategic developments**

This event type captures contextually important information regarding incidents and activities of groups that are not recorded as Political violence or Demonstrations events, yet may trigger future events or contribute to political dynamics within and across states. The inclusion of such events is limited, as their purpose is to capture pivotal events within the broader political landscape. They typically include a disparate range of events, such as recruitment drives, looting, and incursions, as well as the location and date of peace talks and the arrests of high-ranking officials or large groups. While it is rare for fatalities to be reported as a result of such events, they can occur in certain cases — e.g., the suspicious death of a high-ranking official, the accidental detonation of a bomb resulting in the bomber being killed, etc.

Due to their context-specific nature, Strategic developments are not collected and recorded in the same cross-comparable fashion as Political violence and Demonstration events. As such, the Strategic developments event type is primarily a tool for understanding particular contexts (_see this_ [_primer on using Strategic developments_](https://acleddata.com/knowledge-base/strategic-developments-in-the-acled-dataset/)).

The following sub-event types are associated with the Strategic developments event type: Agreement, Arrests, Change to group/activity, Disrupted weapons use, Headquarters or base established, Looting/property destruction, Non-violent transfer of territory, and Other.

_**Agreement**_

This sub-event type is used to record any sort of agreement between different actors (such as governments and rebel groups). Examples include peace agreements/talks, ceasefires, evacuation deals, prisoner exchanges, negotiated territorial transfers, prisoner releases, surrenders, repatriations, etc.

_**Arrests**_

This sub-event type is used when state forces or other actors exercising de facto control over a territory either detain a particularly significant individual or engage in politically significant mass arrests.

_**Change to group/activity**_

This sub-event type is used to record significant changes in the activity or structure of armed groups. It can cover anything from the creation of a new rebel group or a paramilitary wing of the security forces, voluntary recruitment drives, movement of forces, or any other non-violent security measures enacted by armed actors. This sub-event type can also be used if one armed group is absorbed into a different armed group or to track large-scale defections.

_**Disrupted weapons use**_

This sub-event type is used to capture all instances in which an event of Explosions/Remote violence is prevented from occurring, or when armed actors seize significant caches of weapons. It includes the safe defusal of an explosive, the accidental detonation of explosives by those allegedly responsible for planting it, the interception of explosives in the air, as well as the seizure of weapons or weapons platforms such as jets, helicopters, tanks, etc. Note that in cases where a group other than the one that planted an explosive is attempting to render an explosive harmless and it goes off, this is recorded under the Explosions/Remote violence event type, as the explosive has harmed an actor other than the one that planted it.

_**Headquarters or base established**_

This sub-event type is used when an organized armed group establishes a permanent or semi-permanent base or headquarters. There are a few cases where opposition groups other than rebels can also establish a headquarters or base (e.g., AMISOM forces in Somalia).

_**Looting/property destruction**_

This sub-event type is used when actors engage in looting or seizing goods or property outside the context of other forms of violence or destruction, such as rioting or armed clashes. This excludes the seizure or destruction of weapons or weapons systems, which are captured under the ‘Disrupted weapons use’ sub-event type. This can occur during raiding or after the capture of villages or other populated places by armed groups that occur without reported violence.

_**Non-violent transfer of territory**_

This sub-event type is used in situations in which rebels, governments, or their affiliates acquire control of a location without engaging in a violent interaction with another group. Rebels establishing control of a location without any resistance is an example of this event.

_**Other**_

This sub-event type is used to cover any significant development that does not fall into any of the other Strategic developments sub-event types. Examples include the occurrence of a coup, the displacement of a civilian population as a result of fighting, or the discovery of mass graves.

## **Event aggregation**

One or more events can occur in the same location on the same day. If two different types of interactions between the same actors in the same location on the same day are reported, they are typically noted as a single aggregate event. For example:

1. A rebel group fights with government forces in a town and wins control. Rebel artillery strikes are reported throughout the day. In this case, only a single Battles event between the rebels and the government forces is recorded, instead of one Battles event and another Explosions/Remote violence event.
2. On the same day, demonstrators hold peaceful protests that progress into violent clashes with security forces. In this case, a single Riots event is recorded, instead of one Protests event and another Riots event.

ACLED takes steps to avoid double-counting incidents, which can entail the aggregation of different forms of violence into single events. For example, if civilians are killed in the context of a larger Battles event, then these reported fatalities will be added to the total number of fatalities reported for the Battles event. The killing of civilians will be noted in the Notes column of the Battles event, but it will not constitute a separate event. In Battles events, civilians are never recorded as Associated Actors as both parties are armed actors assumed to engage in violence.

Further, if an assault — such as an airstrike — hits a military target, but reports also indicate that civilians were harmed, civilians are recorded as Associated Actors. Similar to the previous case, the fatalities from this event, if reported, are aggregated together. In cases where a bombing occurs with a vague and unspecified military target (e.g., a bombing in a city where some militants are present, rather than an area known to be controlled and actively used by militants), but civilians are the main group affected (e.g., civilians are injured or killed), they will be recorded in the Actor 2 column. Militants may appear in the Associated Actor 1 and Associated Actor 2 columns.

However, if another event type involving different actors occurs on the same day and in the same location, it is recorded separately. Hence, it is possible to have multiple events — involving distinct actors — occur in the same location on the same day. For example, if an incident of armed violence separately targets civilians on the same day and location of a battle (e.g., a group of militants abducts civilians after engaging police in a shootout), two events are recorded to accurately capture the Battles event and the distinct Violence against civilians event.

In most cases, an event requires two actors, noted in columns Actor 1 and Actor 2. However, the Explosions/Remote violence, Riots, Protests, and Strategic developments event types can include one-sided events. If more than two actors are reported, only the most important engagement is recorded, and the additional groups may be recorded as Associated Actors depending on the context (e.g., police forces intervening to disperse rioters). _The order of actors has no meaning in the ACLED dataset_, barring cases of Violence against civilians, in which the target is always recorded as Actor 2.

## **Civilian targeting**

In order to facilitate the analysis of all events in the ACLED dataset that feature violence targeting civilians, the Civilian targeting column allows for filtering of events in which civilians were the main or only target of an event. Besides events coded under the Violence against civilians event type, civilians may also be the main or only target of violence in events coded under the Explosions/Remote violence event type (e.g., a landmine killing a farmer), Riots event type (e.g., a village mob assaulting another villager over a land dispute), and Excessive force against protesters sub-event type (e.g., state forces using lethal force to disperse peaceful protesters). Events in which civilians were incidentally harmed are not included in this category.

## **Actors**

ACLED codes a range of actors, including state forces, rebels, militias, identity groups, demonstrators, civilians, and external or other forces.

The vast majority of political violence events involve organized armed actors, such as government forces and their affiliates, rebel groups, militias, external or private forces (e.g., United Nations missions), and other political groups that interact over issues of political authority (e.g., territorial control, government control, access to resources, etc.). All organized armed actors are named,[6](#footnote6 "Except for the actors marked with “unidentified”, e.g., Unidentified Armed Group or Unidentified Gang.") have a political purpose, and use violence for political means. In order for an actor to be classified as an organized agent of political violence — as opposed to a disorderly riotous group — the organization must be cohesive and assembled for more than a single event. Further, the activity of such an organization must be connected to a means for achieving a larger political purpose. This necessary and sufficient definition of organized actors allows for the establishment of campaigns and trajectories of movements. In contrast to armed organized actors, rioters are considered to be unorganized in the sense that they lack inherent organization beyond spontaneous or atomic acts of organization. Protesters and civilians may be organized and will have named organizations recorded where relevant.

The name of each actor is noted in the Actor 1 and Actor 2 columns of the dataset. The group type is recorded in the Inter 1 and Inter 2 columns, while their dual engagement is noted in the Interaction column.

The Associated Actor 1 and Associated Actor 2 columns record the associated groups for specific events as well as the identity of specific actors. In the former case, an associated group may be an ally in the action — such as two organized armed groups that are engaging in attacks against a common enemy. In the latter case, the Associated Actor 1 and Associated Actor 2 columns may record additional information concerning the targets of an attack, the socio-political affiliation of demonstrators, or the ethno-religious identity of a civilian victim. An Explosions/Remote violence event that destroys the base of an organized armed group, but also affects civilians, will have both groups noted – the primary actor will be the ostensibly-intended target (i.e., the armed group in this case), while civilians (commonly described as "collateral damage" in this case) would be the Associated Actor.[7](#footnote7 "While civilians are recorded as an Associated Actor when they are incidentally killed in Explosions/Remote violence attacks, they are not recorded as such in a Battles event. This is because events under the former involve one side not engaging in any violence within the course of the event; in a Battles event, both sides, by definition, are capable of engaging in or responding with violence, and it would hence be incorrect to denote that civilians are associated with either side.")

### **Actor names, types, and Inter codes**

ACLED records the recognized name of actors as reported, whenever possible. In exceptional circumstances described in detail below, the name of an actor is generated to reflect their origins and composition.

Each named actor is also designated as a type of organization. There are thousands of individually named actors within the ACLED dataset, and the ‘Inter’ code categorizes actors by whether they have similar organizational structures, goals, and practices. Group type designates all actors into one of eight ACLED categories and assigns a code in the Inter 1 and Inter 2 columns to that actor.

These categories offer a way to distinguish between actors and determine how patterns of activity conform to goals and organizations. ACLED does not use a pattern of activity to designate what kind of agent an actor is. _ACLED specifically observes the goals and structure of an actor and, where possible, its spatial dimension and relationships to communities._

As such, the Inter code of an actor can change over time. For example, if a rebel group is successful in overthrowing a regime or seceding from a state, its armed agents may then become the armed wing of a political party within the new regime structure – effectively,  a change in Inter code from Rebel group to Political militia, e.g., the Imbonerakure militia in Burundi — or the government forces of the new state — a change in Inter code from Rebel group to State forces, e.g., the Taliban turned into Afghanistan’s state forces.

Certain types of violent agents may appear to fall outside of this categorization, but ACLED has designed these classifications with the flexibility to fit the universe of agents operating in conflict. For example, militant religious organizations can have various goals (e.g., al-Qaeda), including overtaking the state, influencing political processes and supporting regional political elites, and engaging in communal contests over access to religious sites. _ACLED does not allow for “insurgents” or “terrorists” as types of agents_, but instead categorizes actors as rebels, militias, communal organizations, protesters, etc_._ Many armed organizations may use insurgency tactics or commit acts of violence against civilians, intending to cause a large number of fatalities as part of their violent repertoire. _Instead, ACLED considers the goal and organization of each group to be the basis for their classification._

_**1: State Forces**_

State forces are defined as collective actors, including military and police, that are recognized to perform government functions over a given territory. Government actors are named by ACLED as a series of separate regimes rather than a uniform body. For example, the government regimes in the present-day Democratic Republic of Congo since 1965 are recorded as **Congo/Zaire (1965-1997)**, **Democratic Republic of Congo (1997-2001)**, and **Democratic Republic of Congo (2001-2019)** as opposed to Congo/Zaire (1965-present). As the strength, capacity, and policies of governments can vary widely from one regime to the next, ACLED designates governments by their leading regimes. This enables researchers to capture the differences in government involvement and reaction to violence.

As militaries and police forces are a direct arm of the government, these actors are noted as **Military Forces of State (Year-Year)** or **Police Forces of State (Year-Year)**. Mutinies of militaries are recorded as **Mutiny of Military Forces of State (Year-Year)**. Various units of these state forces are recorded distinctly as well — such as **Police Forces of India (2014-) Assam Rifles** or **Police Forces of the Philippines (2016-) Anti-Illegal Drugs Special Operations Task Force** — given that such units can engage in distinct patterns of behavior. Pro-government militias with _indirect_ links to the state are not included as state forces, given their deliberate distance from formal ties to the state.

It is important to note that this classification of state forces does not imply legitimacy, but rather acknowledges the de facto exercise of authority over a territory. This is why, _in a limited number of cases_, ACLED records government actors in states with limited or no recognition as state forces. These states are not necessarily recorded separately in the Country column, but their government forces are recorded as distinct state actors. For example, the **Military Forces of Somaliland (1991-)** actor is recorded, though its country of activity is recorded in the Country column as Somalia, not Somaliland.

In cases where the authority of a government is severely challenged, or where two or more groups have a claim to be the government (with an associated military), a distinct choice is made about how to proceed with coding — often resulting in both actors being recorded as state forces. For example, there are competing state forces recorded as active in Libya from 2014 onwards and in Yemen from 2015 onwards.

_**2: Rebel Groups**_

Rebel groups are defined as political organizations with the goal of countering an established national governing regime through violence. Rebel groups are named according to the title they publicly use to represent themselves. The designation as a rebel group means that the group has a stated political agenda for national power (either through regime replacement or separatism), is acknowledged beyond the ranks of immediate members, and uses violence as its primary means to pursue political goals.

Rebel forces are known by a specific chosen name and the groups are open and transparent about their intentions and leadership. They typically operate within and across states, and conduct activity against the central governments and their associates. Rebel groups often have predecessors and successors due to diverging goals within their membership. If splinter groups or factions within a group emerge, these are recorded as distinct actors.

In cases where aggregate groups are contesting the government, we often use an overarching name rather than factions (e.g., Hutu Rebels active in Burundi; Malay Muslim Separatists active in Thailand; Opposition Rebels in Syria).

_**3: Political Militias**_

Political militias are a diverse set of violent actors that are often created for a specific purpose or during a specific time period (e.g., the Janjaweed, largely active in Sudan) and for the furtherance of a political goal by violence. Political militias are recorded by their stated name. These organizations are defined by their political goals of influencing and impacting governance, security, and policy. However, these groups are not seeking the removal of a national power, but are instead typically supported, armed by, or allied with a political elite and act toward a goal defined by these elites or larger political movements. Political militias often operate in conjunction, or in alliance, with a recognized government, governor, military leader, rebel organization, political party, business elite, or opposition group. Whereas some opposition parties have a militia arm, groups such as the Sudanese Janjaweed or Serbian Tigers are pro-government militias[8](#footnote8 "Clionadh Raleigh and Roudabeh Kishi, \") that work as supplements to government power yet maintain _indirect_ links to such power.

These groups are not subsumed within the category of government or opposition, but are noted as an armed, distinct, yet associated, wing given their purposeful indirect ties to the state. These political militias may be associated with defined ethnic, regional, or other identity communities, but they also operate outside of ethnic homelands and for goals other than the promotion of ethnic interests. As such, they are recorded as political militias as opposed to identity militias (_more on that below_). The Gulf Clan of Colombia, War Veterans Group in Zimbabwe, and Mayi-Mayi of the Democratic Republic of Congo are examples of these groups.

At times, unidentified armed groups perpetrate political violence. These groups often operate like political militias as they can be used by elites under the cover of anonymity. In some cases, perpetrators are unidentified due to reporting challenges or the absence of detailed information in a particular conflict context; in other – perhaps more common – cases, such groups purposefully work to remain unknown to the larger public in order to pursue violence with impunity. ACLED records such unidentified actors using the name **Unidentified Armed Group (Country)**.[9](#footnote9 "An Unidentified Armed Group is recorded with an Inter code of 3, unless they are Unidentified Military Forces (a rare case that has an Inter code of 1 or 8 depending on the context) or Unidentified Ethnic/Communal/Clan/Tribal Militia with an Inter code of 4, as discussed below.")

_**4: Identity Militias**_

ACLED includes a broad category of identity militias for armed and violent groups organized around a collective, common feature, including: community, ethnicity, region, religion, or — in exceptional cases — livelihood. Therefore, for ACLED’s purposes, identity militias include those identified as tribal, communal, ethnic, local, clan, religious, and caste militias in source reporting. Events involving identity militias are often referred to as communal violence, as these violent groups typically act locally in pursuit of local goals, resources, power, security, and retribution.

An armed group claiming to operate on behalf of a larger identity community may be associated with that community, but not represent it (i.e., Luo Ethnic Militia in Kenya or Fulani Ethnic Militia in Nigeria). Rather, the identity aspect refers to recruitment and participation in these groups being determined by association with the identity of the group.

_**5: Rioters**_

Rioters, loosely assembled groups of individuals or mobs without inherent organization, engage in violence while participating in demonstrations or engage in violence that is spontaneous. While less common, rioters may also include groups that engage in premeditated violence for transient and limited purposes (e.g., a vigilante mob that mobilizes for perceived justice). They are noted by a general category of **Rioters (Country)**. If a named organized group is affiliated with or leading an event (for example, a political party or labor union), the associated group is named in the respective Associated Actor column. Rioters are, by definition, violent or destructive and may engage in a wide array of violent or destructive acts, including property destruction, engaging with other armed groups (e.g., security forces, private security firms, etc.), or in violence against unarmed civilians. While the activity of rioters, by definition, falls outside the remit of an organized armed group, rioters may sometimes be armed and/or organized in a spontaneous or atomic manner.

_**6: Protesters**_

Protesters are peaceful demonstrators,[10](#footnote10 "Though non-violent, protesters may engage in disruptive behavior like burning effigies or shoe-throwing.") noted by a general category of **Protesters (Country).** If a group is affiliated with or leading an event (e.g., Movement for Democratic Change political party), the associated group is named in the respective Associated Actor column. Although protesters are non-violent, they may be the targets of violence by other groups (e.g. security institutions, private security firms, or other armed actors).

_**7: Civilians**_

Civilians, in whatever number or association, are victims of violent acts within ACLED as they are — by definition — unarmed and, hence, vulnerable. They are noted as **Civilians (Country)**. If targeted with violence in situations where they are caught unarmed, some normally armed actors may be recorded as civilians. Examples include off-duty state soldiers targeted in their homes, or members of armed groups subject to violence or executed while imprisoned.

_**8: External/Other Forces**_

Small categories of external or other actors include: international organizations, state forces active outside of their main country of operation, private security firms and their armed employees, and hired mercenaries acting independently. They are noted by their name and actions. The military forces of states are recorded with an Inter code of 8 (i.e.,  external forces) when active outside of their home state (e.g., the military of Turkey active in northern Syria).

### **Interaction codes**

The joined Interaction code is the combination of the two Inter codes associated with the two main actors in an event. Single actor type codes are recorded in Inter 1 and Inter 2 columns, and the compounded value is recorded in the Interaction column. For example, if a country’s military fights a political militia group, and the respective Inter 1 and Inter 2 codes are State forces and ‘Political militia’, respectively, the compounded ‘Interaction’ code is recorded as State forces-Political militia.

Interaction codes are standardized so the order of the Actor 1 and Actor 2 does not matter across events: e.g., State forces engaging with Political militias and Political militias engaging with State forces are all recorded as State forces – Political militia.

Interaction’ codes are recorded for all events, including non-violent activity. For one-sided events, the empty Actor 2 column is recorded as a blank value. For example, if an event involving a rebel group is non-violent, the Inter 1 code is Rebel group, and Rebel group only is recorded in the Interaction column. Only the actors recorded in the Actor 1 and Actor 2 columns form the basis for the Interaction code of an event, and not the actors recorded in the Associated Actors columns.

_Table 3: Interaction code descriptions_

**Interaction code**

**Description**

10: State forces only

SOLE STATE FORCES ACTION (e.g., base establishment by state forces; remote violence involving state military with no reported casualties; non-violent military operations)

11: State forces-State forces

STATE FORCES VERSUS STATE FORCES (e.g., military infighting; battles between a military and mutinous forces; arrests of military officials)

12: State forces-Rebel group

STATE FORCES VERSUS REBELS (e.g., civil war violence between state forces and a rebel actor)

13: State forces-Political militia

STATE FORCES VERSUS POLITICAL MILITIA (e.g., violence between state forces and unidentified armed groups; violence between police and political party militias)

14: State forces-Identity militia

STATE FORCES VERSUS IDENTITY MILITIA (e.g., military engagement with a communal militia)

15: State forces-Rioters

STATE FORCES VERSUS RIOTERS (e.g., suppression of a violent demonstration by police or military)

16: State forces-Protesters

STATE FORCES VERSUS PROTESTERS (e.g., suppression of a peaceful demonstration by police or military)

17: State forces-Civilians

STATE FORCES VERSUS CIVILIANS (e.g., state repression of civilians; arrests by police)

18: State forces-External/Other forces

STATE FORCES VERSUS EXTERNAL/OTHER FORCES (e.g., inter-state conflict; state engagement with private security forces or a UN operation; strategic developments between a regime and the UN or another external actor)

20: Rebel group only

SOLE REBEL ACTION (e.g., base establishment; remote violence involving rebel groups with no reported target; accidental detonation by a rebel group)

22: Rebel group-Rebel group

REBELS VERSUS REBELS (e.g., rebel infighting; violence between rebel groups and their splinter movements)

23: Rebel group-Political militia

REBELS VERSUS POLITICAL MILITIA (e.g., civil war violence between rebels and a pro-government militia; violence between rebels and unidentified armed groups)

24: Rebel group-Identity militia

REBELS VERSUS IDENTITY MILITIA (e.g., violence between rebels and local security providers)

25: Rebel group-Rioters

REBELS VERSUS RIOTERS (e.g., spontaneous violence against a rebel group; a violent demonstration engaging a rebel group)

26: Rebel group-Protesters

REBELS VERSUS PROTESTERS (e.g., violence against protesters by rebels)

27: Rebel group-Civilians

REBELS VERSUS CIVILIANS (e.g., rebel targeting of civilians \[a strategy commonly used in civil war\])

28: Rebel group-External/Other forces

REBELS VERSUS OTHERS (e.g., civil war violence between rebels and an allied state military; rebel violence against a UN operation)

30: Political militia only

SOLE POLITICAL MILITIA ACTION (e.g., remote violence by an unidentified armed group with no reported target; accidental detonation by a political militia; strategic arson as intimidation by a political party)

33: Political militia-Political militia

POLITICAL MILITIA VERSUS POLITICAL MILITIA (e.g., inter-elite violence)

34: Political militia-Identity militia

POLITICAL MILITIA VERSUS IDENTITY MILITIA (e.g., violence between communal militia and an unidentified armed group; violence between political militia and local security providers)

35: Political militia-Rioters

POLITICAL MILITIA VERSUS RIOTERS (e.g., violent demonstration against a political militia; spontaneous violence against a political militia)

36: Political militia-Protesters

POLITICAL MILITIA VERSUS PROTESTERS (e.g., suppression of a peaceful demonstration by a political militia)

37: Political militia-Civilians

POLITICAL MILITIA VERSUS CIVILIANS (e.g., out-sourced state repression carried out by pro-government militias; civilian targeting by political militias or unidentified armed groups)

38: Political militia-External/Other forces

POLITICAL MILITIA VERSUS OTHERS (e.g., violence between private security forces and unidentified armed groups; violence between pro-government militia and external state military forces)

40: Identity militia only

SOLE IDENTITY MILITIA ACTION (e.g., destruction of property by a communal militia; establishment of a local security militia)

44: Identity militia-Identity militia

IDENTITY MILITIA VERSUS IDENTITY MILITIA (e.g., inter-communal violence)

45: Identity militia-Rioters

IDENTITY MILITIA VERSUS RIOTERS (e.g., violent demonstration against an identity militia; spontaneous violence against an identity militia)

46: Identity militia-Protesters

IDENTITY MILITIA VERSUS PROTESTERS (e.g., suppression of a peaceful demonstration by  an identity militia)

47: Identity militia-Civilians

IDENTITY MILITIA VERSUS CIVILIANS (e.g., civilian targeting, especially in the context of inter-communal violence)

48: Identity militia-External/Other forces

IDENTITY MILITIA VERSUS OTHER (e.g., external state military engaging in violence against a communal militia)

50: Rioters only

SOLE RIOTER ACTION (e.g., one-sided violent demonstration; spontaneous arson)

55: Rioters-Rioters

RIOTERS VERSUS RIOTERS (e.g., two-sided violent demonstration in which both sides engage in violence)

56: Rioters-Protesters

RIOTERS VERSUS PROTESTERS (e.g., two-sided demonstration in which only one side engages in violence)

57: Rioters-Civilians

RIOTERS VERSUS CIVILIANS (e.g., violent demonstration in which civilians are injured/killed; spontaneous violence in which civilians are targeted by a mob)

58: Rioters-External/Other forces

RIOTERS VERSUS OTHERS (e.g., mob violence against regional or international operation)

60: Protesters only

SOLE PROTESTER ACTION (e.g., one-sided peaceful protest)

66: Protesters-Protesters

PROTESTERS VERSUS PROTESTERS (e.g., two-sided peaceful protest)

67: Protesters-Civilians

PROTESTERS VERSUS CIVILIANS (e.g., peaceful protesters engaging civilians)

68: Protesters-External/Other forces

PROTESTERS VERSUS OTHER (e.g., suppression of a peaceful demonstration by private security forces)

70: Civilians only

SOLE CIVILIAN ACTION (e.g., one-sided strategic development)

77: Civilians-Civilians

CIVILIANS VERSUS CIVILIANS (e.g., peaceful interactions between civilians recorded as ‘Strategic developments’)

78: External/Other forces-Civilians

OTHER ACTOR VERSUS CIVILIANS (e.g., regional or international operation targeting civilians; private security forces targeting civilians)

80: External/Other forces only

SOLE OTHER ACTION (e.g., strategic developments involving international or regional operations; remote violence by external military forces with no reported target; non-violent external military operations)

88: External/Other forces-External/Other forces

OTHER VERSUS OTHER (e.g., clashes between foreign state forces, international missions, or private security forces)

## **Event geography**

There are up to six different types of spatial information that can be recorded for each ACLED event:

1. The continental sub-region in which the event occurred.
2. The country in which the event occurred and its associated ISO code.
3. The name of the _first_, _second,_ and _third_ level administrative zones in which the specific location is found, according to GIS-based assessments and updated administrative codes.
4. The name of the specific location of an event.
5. The geographic coordinates of that specific location.
6. A spatial precision code.

The most specific location for an event for each event ACLED records is sought, using multiple sources to triangulate better location information.

Locations are recorded to named populated places, geostrategic locations, natural locations, or neighborhoods of larger cities. Geo-coordinates with four decimals are provided to assist in identifying and mapping named locations to a central point (i.e., a centroid coordinate) within that location. Geo-coordinates do not reflect a more precise location, like a block or street corner, within the named location.

In selected large cities with activity dispersed over many neighborhoods, locations are further specified to predefined subsections within a city to prevent excessive aggregation of events to a single city location. In such cases, locations are recorded as: **City Name – District name** (e.g., Mosul – Old City) in the Location column. If information about the specific neighborhood/district is not known, the location is recorded at the city level (e.g., Mosul). In both cases, Geo-precision code 1 is recorded _(see the section on_ [_spatial precision codes_](https://acleddata.com/knowledge-base/codebook/#spatial-precision-codes)). The hyphenation feature allows users to aggregate events by city, if needed.

### _**Spatial precision codes**_

If the source reporting indicates a particular town, and coordinates are available for that town, the highest precision level, Geo-precision code 1, is recorded. If the source material indicates that activity took place in a small part of a region, and mentions a general area, the event is coded to a town with geo-referenced coordinates to represent that area, and the ‘Geo-precision’ code 2 is recorded. If activity occurs near a town or a city, the same Geo-precision code 2 is employed. If a larger region is mentioned, the closest natural location noted in reporting (like “border area,” “forest,” or “sea,” among others) — or a provincial capital is used if no other information at all is available — is chosen to represent the region, and Geo-precision code 3 is recorded. Barring some Strategic developments events, ACLED does not record events that are imprecise to the country level — meaning reports that mention 1,000 conflict fatalities “across the country” will be investigated until they can be recorded as a set of more specific events and will not be recorded as a single countrywide event.

## **Event Time**

Three forms of temporal information are found in each ACLED code:

1. The date of each event.
2. The year.
3. The temporal precision.

Dates are a necessary component of all ACLED events. ACLED events are atomic as events are recorded by day. If a military campaign in an area starts on 1 March 2020 and lasts until 5 March 2020 with violent activity reported on each day, this is recorded as five different events, with a different date for each entry. This episode would not be entered as a single campaign of violence. This allows ACLED to record the exact number of active days of a conflict. Events that the source material indicates as occurring in the space of three months — such as long-running protests — are not automatically assumed to have 90 days of activity, but instead are only recorded for the days for which it is specifically reported that an activity took place. This avoids over-counting event occurrences.

### _**Time precision codes**_

If the source material includes an actual date of an event, a Time precision code of 1 is recorded. If the source material indicates that an event happened sometime during the week or within a similar period of time (i.e., during the weekend), a Time precision code of 2 is recorded and the middle of the period is used as the reference date (i.e., with an event occurring last week, the Event date would be recorded on either Wednesday or Thursday of that week). If the source material only indicates that an event took place sometime during a month (i.e., in the past two or three weeks, or in January), without reference to the particular date, the month midpoint is chosen. If the beginning or end of the month is noted, the first and last date is used, respectively. In both of these cases, a Time precision code of 3 is recorded. ACLED does not include events with less temporal information.

## **Reported fatalities**

Events that result in fatalities have the relevant information recorded in the Fatalities column. _Events recorded by ACLED do not have to meet a minimum fatality number for inclusion_. ACLED only records estimated fatalities when reported by the source material. When and where possible, ACLED researchers seek out information to triangulate the fatality numbers reported by sources, but ACLED does not independently verify reported fatality estimates. Additionally, ACLED is a living dataset, so all fatality figures are revised and corrected — upward or downward — if new or better information becomes available (which, in some cases, can be months or years after an event has taken place). Fatality data are typically the most biased and least accurate component of conflict reporting. They are particularly prone to manipulation by armed groups, and occasionally the media, which may overstate or underreport fatalities for political purposes. These figures should therefore be understood as indicative estimates of _reported_ fatalities, rather than definitive fatality counts.

If the source material differs or a vague estimate is provided, the lowest number of reported fatalities is recorded in the Fatalities column until a more reliable or corroborated estimate becomes available. If reports mention “several,” “many,” “few,” or plural “fatalities,” yet the exact number is unknown, either 3 or 10 is recorded as the total, depending on the scale and context of the attack (_for more, see_ [_FAQs: ACLED Fatality Methodology_](https://acleddata.com/knowledge-base/faqs-acled-fatality-methodology/)). If a report mentions “dozens,” this is recorded as 12 reported fatalities. If a report mentions “hundreds,” this is recorded as 100 reported fatalities. If there is no reference made to fatalities in the source material, or if it is unclear whether fatalities occurred at all (for example, when only “casualties” are mentioned, which — by definition — means injuries and/or fatalities), 0 reported fatalities are recorded.

When summarized fatalities are reported, but events occur across several days or in multiple locations simultaneously (e.g., “12 fatalities result from fighting over a span of 3 days”), the total number of reported fatalities is divided and that fraction is recorded for each day of the event (4 reported fatalities per battle day, in the example above). If an odd number of fatalities is recorded (including 1), the proportion of reported fatalities is divided by assigning the first day the additional fatality and it is then distributed as evenly as possible. The disaggregation of fatalities is recorded in the Notes column of the relevant events.

## **Notes**

The Notes column summarizes the main features of the event. Notes are kept short and limited to significant details about the specific event. In rare cases, additional relevant information is added to provide context to the event.

## **Tags**

The Tags column provides additional structured information about an ACLED event. Tags provide a flexible means of refining or grouping existing variables, or providing new variables for specific contexts that are not already captured within the other data columns. Tags can be specific to certain actors and event types, themes, countries, time periods, etc, or combinations thereof. As such, some tags are hyperspecific, such as the “count every vote” tag that was introduced for the 2020 election demonstrations in the United States. Other tags, like the “crowd size” tag, are applied globally to all Protests and Riots events. Tags can be introduced or retired as situations on the ground and analytical needs develop or subside.

Each tag is separated by a semicolon (;) in the Tags column. Users may filter by the tags to quickly generate subsets of the data on specific political violence or demonstration activity _(for more on how tags are added to the ACLED dataset and the full list of tags, see_ [_Tags in ACLED Data_](https://acleddata.com/knowledge-base/tags-in-the-data/)_)._

## **Sources and Information Sourcing**

ACLED collects information from four main types of sources:

1. **Traditional media**: This includes all subnational, national, regional, and international media outlets that are governed by journalistic principles of verification.
2. **Reports**: International institutions and non-governmental organizations – such as aid groups, human rights organizations, and investigative journalism groups – regularly publish reports on political violence. Where applicable, ACLED incorporates events from these reports. Under certain conditions, reports from groups involved in conflict themselves are also included (Ministries of Defense, armed groups, NATO, etc.).
3. **Local partner data:** The past decades have seen an increase in organizations established at the local level as both social activism and the ability to report political violence have increased. These organizations leverage their local knowledge as they collect and obtain information through primary and/or secondary means. ACLED develops relationships with local partners to enhance the depth and quality of its data.[11](#footnote11 "For safety reasons, some partners that wish to remain anonymous are recorded as \")
4. **New nedia (targeted and verified):** New media (e.g., Twitter, Telegram, WhatsApp) can be a powerful supplemental source, but varies widely in terms of quality. Therefore, _ACLED does not crowdsource or scrape large amounts of social media._ Rather, a targeted approach to the inclusion of new media is preferred through either the establishment of relationships with the source directly, or the verification of the quality of each source.

ACLED researchers systematically cover thousands of distinct sources in over 75 languages. Sourcing lists are carefully curated and monitored to maintain accurate coverage _(for more, see_ [_FAQS: ACLED Sourcing Methodology_](https://acleddata.com/knowledge-base/faqs-acled-sourcing-methodology/)_)._

Every ACLED event is based on at least one source. The source names or acronyms are noted in the Source column. With the exception of certain local sources that wish to remain anonymous, the Source column details are sufficient to retrace the sources that have been used to record an event. All sources listed have contributed information to the event. Researchers often find multiple reports confirming details about an event; when multiple sources report on the same information, the most thorough, reliable, and recent report is cited.

If that event has additional information taken from more than one source, both report sources are noted in the Source column.

### **Source scale**

The Source scale column describes whether the sources used for coding an event operate at the local, subnational, national, regional, international, or other level. ACLED develops tailored sourcing profiles for different conflict and disorder contexts, drawing on sources across various scales. An integral part of this sourcing strategy is ACLED’s unique network of local data collection partners and observatories around the world. With this network, ACLED is able to gather information in hard-to-access contexts and integrate additional thematic, regional, and country-level expertise into the dataset _(for more, see_ [_FAQS: ACLED Sourcing Methodology_](https://acleddata.com/knowledge-base/faqs-acled-sourcing-methodology/)_)_. 
 

## **Relationship to other datasets**

Information collected by ACLED is generally compatible with other conflict datasets. ACLED data may be combined with many, if not all, other conflict datasets by country, year, actor, or specific locality. _ACLED data are event data and, as such, care should be given to combining the information in the ACLED dataset with other datasets using different units of analysis (e.g., campaigns of violence instead of violent events by day)._

As ACLED records a wide range of constituent events for periods and areas affected by political violence and disorder, more information is collected than datasets that focus on specific forms of violence (e.g., civil war, terrorism as defined by targeting of civilians by non-state actors alone, or those with fatality thresholds for inclusion) or campaigns of violence rather than events. Please note that ACLED is a living dataset and event details are subject to change as new or better information becomes available. Results of analysis based on ACLED data may differ from analysis based on other datasets with different scopes and methodologies.

Versions 1 to 7 of the ACLED dataset covered African states. Version 8 expanded to include South and Southeast Asia and the Middle East. Codebooks for earlier versions of the ACLED dataset are available upon request. Following Version 8, ACLED moved to a system of updating events with corrections and appending supplemental data as necessary in real time. Therefore, ACLED no longer releases formal versions. In 2022, ACLED completed a final geographic coverage expansion, extending data collection to the entire world.

Close footnote

## Footnotes

1. [1](#footnoteref1)

   ACLED includes organized criminal violence as political violence when it challenges safety, security, and territorial control within a state. For more on this, see the [ACLED Gang Methodology](https://acleddata.com/knowledge-base/gang-violence-concepts-benchmarks-and-coding-rules/).
2. [2](#footnoteref2)

   ACLED also does not categorize clusters or campaigns of events into categories of state or non-state operations, terrorism, insurgency, etc. This is because political violence, demonstrations, conflict, and disorder are aggregations of multiple actors, attacks, goals, etc. Classifying events into parts of a civil war, livelihood, religious, or election conflict (to name a few common versions) is often a reductive choice, leaving out the complex ways conflict creates multiple scales of violence and intended outcomes within a territory.
3. [3](#footnoteref3)

   With the sole exception of Unidentified Armed Group and generic categories including Rioters, Protesters, and Civilians.
4. [4](#footnoteref4)

   Dispersal orders or citations, in the absence of reports of physical action to detain or remove protesters, are not captured under this sub-event type; if protesters are only issued citations, the event would be coded as a Peaceful protest.
5. [5](#footnoteref5)

   In rare cases where non-state groups are able to maintain some level of judicial/penal system, they are also considered able to engage in Arrests, and these actions are not recorded as Abduction/forced disappearance and are instead recorded under the Arrests sub-event type.
6. [6](#footnoteref6)

   Except for the actors marked with “unidentified”, e.g., **Unidentified Armed Group** or **Unidentified Gang**.
7. [7](#footnoteref7)

   While civilians are recorded as an Associated Actor when they are incidentally killed in Explosions/Remote violence attacks, they are not recorded as such in a Battles event. This is because events under the former involve one side not engaging in any violence within the course of the event; in a Battles event, both sides, by definition, are capable of engaging in or responding with violence, and it would hence be incorrect to denote that civilians are associated with either side.
8. [8](#footnoteref8)

   [Clionadh Raleigh and Roudabeh Kishi, &#34;Hired Guns; Using Pro-Government Militias for Political Competition,&#34; Terrorism and Political Violence, 8 January 2018](https://www.tandfonline.com/doi/citedby/10.1080/09546553.2017.1388793?scroll=top&needAccess=true&role=tab "(opens in a new window)")
9. [9](#footnoteref9)

   An Unidentified Armed Group is recorded with an Inter code of 3, unless they are Unidentified Military Forces (a rare case that has an Inter code of 1 or 8 depending on the context) or Unidentified Ethnic/Communal/Clan/Tribal Militia with an Inter code of 4, as discussed below.
10. [10](#footnoteref10)

    Though non-violent, protesters may engage in disruptive behavior like burning effigies or shoe-throwing.

11. [11](#footnoteref11)

    For safety reasons, some partners that wish to remain anonymous are recorded as "Undisclosed Source" in the Source column.

Region

[Global](/region/global)

Share on

Share to social media

- [X](https://twitter.com/intent/tweet?text=ACLED%20Codebook&via=ACLEDINFO&url=https://acleddata.com/methodology/acled-codebook "(opens in a new window)")

- [Facebook](https://www.facebook.com/sharer/sharer.php?u=https://acleddata.com/methodology/acled-codebook "(opens in a new window)")
- [Linkedin](https://www.linkedin.com/sharing/share-offsite/?url=https://acleddata.com/methodology/acled-codebook "(opens in a new window)")

## Related content

[How to Analyze ACLED’s Notes Column using Natural Language Processing (NLP)](/methodology/how-analyze-acleds-notes-column-using-natural-language-processing-nlp)

![](/themes/custom/acled/assets/img/card-fallback-image.svg)

[Overview of ACLED’s data enhancement projects and known data limitations](/methodology/overview-acleds-data-enhancement-projects-and-known-data-limitations)

18 October 2024

[How does ACLED code and review data to ensure quality?](/methodology/how-does-acled-code-and-review-data-ensure-quality)

![](/themes/custom/acled/assets/img/card-fallback-image.svg)

[Strategic Developments in the ACLED Dataset](/methodology/strategic-developments-acled-dataset)

![](/themes/custom/acled/assets/img/card-fallback-image.svg)
